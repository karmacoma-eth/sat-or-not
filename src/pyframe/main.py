import cairosvg
import io
import logging
import textwrap

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from multidict import MultiDict
from typing import Annotated
from yarl import URL

from .logic import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# LOGICAL_AND = "&amp;#x2227;"
# LOGICAL_OR = "&amp;#x2228;"

# LOGICAL_AND = "∧"
# LOGICAL_OR = "∨"

LOGICAL_AND = "&amp;"
LOGICAL_OR = "|"

SAT_BUTTON_ID = 1
NOT_SAT_BUTTON_ID = 2

@app.get("/")
def root(request: Request):
    """
    Just a splash screen with a PLAY button that redirects to /play.
    """

    base_url = str(request.base_url)
    banner_url = URL(base_url) / "static" / "sat-or-not-banner.png"
    play_url = URL(base_url) / "play"

    return HTMLResponse(
        status_code=200,
        content=textwrap.dedent(f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>SAT or NOT</title>
                    <meta property="og:title" content="SAT or NOT" />
                    <meta property="og:image" content="{banner_url}" />
                    <meta property="fc:frame:image" content="{banner_url}" />
                    <meta property="fc:frame" content="vNext" />
                    <meta property="fc:frame:button:1" content="PLAY" />
                    <meta property="fc:frame:post_url" content="{base_url}play" />
                </head>
                <body>
                    <div>
                        <img src="{banner_url}" alt="SAT or NOT" style="width: 100%; max-width: 1024px;">
                    </div>
                    <div>
                        <a href="{play_url}">PLAY</a>
                    </div>
                </body>
            </html>
        """)
    )


def as_multidict(clauses: list[tuple[int]]) -> MultiDict:
    tuples_as_strings = ['.'.join(str(x) for x in clause) for clause in clauses]
    query_params = [('clauses', t) for t in tuples_as_strings]
    return MultiDict(query_params)


def parse(encoded_clauses: list[str]) -> list[tuple[int]]:
    # ex: ['1.3.1', '1.2.1'] -> [(1, 3, 1), (1, 2, 1)]
    return [tuple(int(x) for x in clause.split('.')) for clause in encoded_clauses]


@app.post("/play")
@app.get("/play")
def play(request: Request):
    """
    Generates a new problem, renders it (via /problem_image) and presents 2 buttons:
    - SAT
    - NOT SAT
    Both send the user to /verify with the chosen option.
    """

    base_url = URL(str(request.base_url))
    problem = generate_msat_instance(3, 3, 6)
    problem_multidict = as_multidict(problem)

    # TODO: add timestamp to bust caching
    problem_image_url = base_url / "problem_image" % problem_multidict
    verify_url = base_url / "verify" % problem_multidict

    return HTMLResponse(
        status_code=200,
        content=textwrap.dedent(f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>SAT or NOT</title>
                    <meta property="og:title" content="SAT or NOT" />

                    <meta property="fc:frame:image" content="{problem_image_url}" />

                    <meta property="fc:frame" content="vNext" />
                    <meta property="fc:frame:button:{SAT_BUTTON_ID}" content="SAT" />
                    <meta property="fc:frame:button:{NOT_SAT_BUTTON_ID}" content="NOT SAT" />

                    <meta property="fc:frame:post_url" content="{verify_url}" />
                </head>
                <body>
                    <!-- for local testing -->
                    <img src="{problem_image_url}" alt="SAT or NOT" style="width: 100%; max-width: 1024px;">
                    <form action="{verify_url % {'button_index': 1}}" method="POST">
                        <button type="submit">SAT</button>
                    </form>
                    <form action="{verify_url % {'button_index': 2}}" method="POST">
                        <button type="submit">NOT SAT</button>
                    </form>
                </body>
            </html>
        """)
    )

@app.post("/verify")
@app.get("/verify")
async def verify(
        request: Request, clauses: Annotated[list[str] | None, Query()] = None,
        button_index: Annotated[int | None, Query()] = None):

    if not clauses:
        return "No clauses provided", 400

    content_type = request.headers.get('content-type')
    logger.debug(f"Content-Type: {content_type}")
    if content_type == 'application/json':
        body = await request.json()
        button_index = body['untrustedData']['buttonIndex']

    if button_index not in (SAT_BUTTON_ID, NOT_SAT_BUTTON_ID):
        return "Invalid button index", 400

    # TODO: verify user data

    expected = 'sat' if button_index == SAT_BUTTON_ID else 'unsat'
    parsed_clauses = parse(clauses)
    model = solve_cnf_instance(parsed_clauses)

    actual = 'sat' if model is not None else 'unsat'
    correct = actual == expected

    model_dict = {str(d): model[d] for d in model.decls()}

    base_url = URL(str(request.base_url))
    parsed_clauses = parse(clauses)
    result_image_url = base_url / "result_image" % as_multidict(parsed_clauses) % {'model': model_dict, 'correct': correct}
    play_url = base_url / "play"
    play_label = "PLAY AGAIN"

    return HTMLResponse(
        status_code=200,
        content=textwrap.dedent(f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>SAT or NOT</title>
                    <meta property="og:title" content="SAT or NOT" />
                    <meta property="og:image" content="{result_image_url}" />
                    <meta property="fc:frame:image" content="{result_image_url}" />
                    <meta property="fc:frame" content="vNext" />
                    <meta property="fc:frame:button:1" content="{play_label}" />
                    <meta property="fc:frame:post_url" content="{play_url}" />
                </head>
                <body>
                    <div>
                        <img src="{result_image_url}" alt="results" style="width: 100%; max-width: 1024px;">
                    </div>
                    <div>
                        <a href="{play_url}">{play_label}</a>
                    </div>
                </body>
            </html>
        """)
    )



@app.get("/problem_image")
async def problem_image(clauses: Annotated[list[str] | None, Query()] = None):
    # TODO: add timestamp to bust caching
    if not clauses:
        return "No clauses provided", 400

    parsed_clauses = parse(clauses)
    clause_strings = [render_clause(clause, or_symbol=LOGICAL_OR) for clause in parsed_clauses]
    clause_strings[1:] = [f"{LOGICAL_AND} " + clause for clause in clause_strings[1:]]
    svg_clause_strings = [f'<text x="35%" y="{18 + i * 14}%" font-size="120" font-family="Arial" fill="white">{clause}</text>' for i, clause in enumerate(clause_strings)]

    svg_content = f'''<svg width="1910" height="1000" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="black" />
        {'\n    '.join(svg_clause_strings)}
    </svg>'''

    # Convert SVG to PNG
    png_content = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))

    # Return the PNG content in a StreamingResponse, setting the media type to image/png
    return StreamingResponse(io.BytesIO(png_content), media_type="image/png")


@app.get("/result_image")
async def result_image(model: dict, correct: bool, clauses: Annotated[list[str] | None, Query()] = None):
    # TODO: add timestamp to bust caching

    if not clauses:
        return "No clauses provided", 400

    result_svg = f'<text x="35%" y="50%" font-size="120" font-family="Arial" fill="{'green' if correct else 'red'}">{'Correct!' if correct else 'WRONG'}</text>'

    parsed_clauses = parse(clauses)
    clause_strings = [render_clause(clause, or_symbol=LOGICAL_OR) for clause in parsed_clauses]
    clause_strings[1:] = [f"{LOGICAL_AND} " + clause for clause in clause_strings[1:]]
    svg_clause_strings = [f'<text x="35%" y="{18 + i * 14}%" font-size="90" font-family="Arial" fill="white">{clause}</text>' for i, clause in enumerate(clause_strings)]

    if model is None:
        model_svg = f'<text x="35%" y="70%" font-size="90" font-family="Arial" fill="white">is UNSAT</text>'
    else:
        model_svg = f'<text x="35%" y="70%" font-size="90" font-family="Arial" fill="white">is SAT with model {model}</text>'

    svg_content = f'''
    <svg width="1910" height="1000" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="black" />
        {result_svg}
        {'\n    '.join(svg_clause_strings)}
        {model_svg}
    </svg>
    '''

    # Convert SVG to PNG
    png_content = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))

    # Return the PNG content in a StreamingResponse, setting the media type to image/png
    return StreamingResponse(io.BytesIO(png_content), media_type="image/png")

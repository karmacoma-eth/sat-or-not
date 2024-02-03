import cairosvg
import io
import logging
import textwrap

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from urllib.parse import urlencode

from .logic import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# LOGICAL_AND = "&amp;#x2227;"
# LOGICAL_OR = "&amp;#x2228;"

# LOGICAL_AND = "∧"
# LOGICAL_OR = "∨"

LOGICAL_AND = "&amp;"
LOGICAL_OR = "|"

@app.get("/")
def root(request: Request):
    base_url = request.base_url
    banner = f"{base_url}static/sat-or-not-banner.png"
    return HTMLResponse(
        status_code=200,
        content=textwrap.dedent(f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>SAT or NOT</title>
                    <meta property="og:title" content="SAT or NOT" />
                    <meta property="og:image" content="{banner}" />
                    <meta property="fc:frame:image" content="{banner}" />
                    <meta property="fc:frame" content="vNext" />
                    <meta property="fc:frame:button:1" content="PLAY" />
                    <meta property="fc:frame:post_url" content="{base_url}play" />
                </head>
                <body>
                    <img src="{banner}" alt="SAT or NOT" style="width: 100%; max-width: 1024px;">
                </body>
            </html>
        """)
    )


def encode(clauses):
    # Convert each tuple into a string representation, assuming that's how you want to pass them
    # This step might vary based on how the receiving end expects to parse them
    tuples_as_strings = ['.'.join(map(str, t)) for t in clauses]

    # Prepare the data for urlencode by pairing each stringified tuple with a common key
    query_params = [('clauses', t) for t in tuples_as_strings]

    # URL-encode the query parameters
    encoded_query_string = urlencode(query_params, doseq=True)
    return encoded_query_string


def parse(encoded_clauses):
    # Parse the query string into a list of tuples
    return [tuple(map(int, clause.split('.')) for clause in encoded_clauses)]


@app.get("/play")
def play(request: Request):
    base_url = request.base_url
    problem = generate_msat_instance(3, 3, 6)
    encoded_problem = encode(problem)
    problem_image_url = f"{base_url}problem_image?{encoded_problem}"

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
                    <meta property="fc:frame:button:1" content="SAT" />
                    <meta property="fc:frame:button:2" content="NOT" />

                    <meta property="fc:frame:post_url" content="{base_url}play" />
                </head>
                <body>
                    <img src="{problem_image_url}" alt="SAT or NOT" style="width: 100%; max-width: 1024px;">
                </body>
            </html>
        """)
    )


@app.get("/problem_image")
async def number_image(clauses: Annotated[list[str] | None, Query()] = None):
    if not clauses:
        return "No clauses provided", 400

    parsed_clauses = parse(clauses)
    clause_strings = [render_clause(clause, or_symbol=LOGICAL_OR) for clause in parsed_clauses]
    clause_strings[1:] = [f"{LOGICAL_AND} " + clause for clause in clause_strings[1:]]
    svg_clause_strings = [f'<text x="35%" y="{18 + i * 14}%" font-size="120" font-family="Arial" fill="white">{clause}</text>' for i, clause in enumerate(clause_strings)]

    # Create an SVG content with the number
    svg_content = f'''<svg width="1910" height="1000" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="black" />
        {'\n    '.join(svg_clause_strings)}
    </svg>'''

    # Convert SVG to PNG
    png_content = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))

    # Return the PNG content in a StreamingResponse, setting the media type to image/png
    return StreamingResponse(io.BytesIO(png_content), media_type="image/png")



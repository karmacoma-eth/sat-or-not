# sat-or-not

hacking on Farcaster frames in Python

```sh
# run the app as a local web server
rye run uvicorn satnot.main:app --reload
```

## Testing

Testing locally:

```sh
# run the local web server, then
open http://127.0.0.1:8000

# click around, requests are accessible via GET to support local testing
```

## Deploying

On Render:

```sh
# build
pip install -r requirements.lock

# deploy
uvicorn satnot.main:app --host 0.0.0.0 --port 10000
```


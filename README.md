# pyframe
hacking on Farcaster frames in Python


```sh
# run the FastAPI app directly
rye run hello

# run the app as a local web server
rye run uvicorn pyframe.main:app --reload
```

## Deploying

On Render:

```sh
# build
pip install -r requirements.lock

# deploy
uvicorn pyframe.main:app --host 0.0.0.0 --port 10000
```

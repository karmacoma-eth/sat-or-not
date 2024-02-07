# sat-or-not

[Play it](https://warpcast.com/karma/0x5df8b239)

As a [Frame](https://docs.farcaster.xyz/reference/frames/spec), the buttons are wired like this:

```
               ┌───┐
     ┌─────────┤ / ├────────┐
     │         └───┘        │
     │   oc_image: banner   │
     │   button: PLAY       │
     │                      │
     └──────────────────────┘
                 │
                 │
                 ▼
              ┌─────┐
┌─────────────┤/play├────────────┐
│             └─────┘            │
│   oc_image: problem_image?...  │
│   button1: SAT                 │◀────┐
│   button2: NOT SAT             │     │
│                                │     │
└────────────────────────────────┘     │
                 │                     │
                 │                     │
                 │                     │
                 ▼                     │
            ┌────────┐                 │
┌───────────┤/verify ├───────────┐     │
│           └────────┘           │     │
│   oc_image: verify_image?...   │     │
│   button: PLAY                 │     │
│                                │     │
└────────────────────────────────┘     │
                 │                     │
                 │                     │
                 └─────────────────────┘
```

In `/play`, we generate a random 3SAT instance.
In `/verify`, we call the solver to check if the instance is sat or unsat, and match it with the provided answer.
In `/verify_image`, we render the 3SAT instance, the "right or wrong" text and the assignment if there is one.


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

Validate the deployment is correct on https://warpcast.com/~/developers/frames

import sys
import uvicorn

"""
python3 run.py NO 8000

python3 run.py deploy

"""

if __name__ == "__main__":

    print(sys.argv)
    try:
        ENABLE_DEPLOY = False
        DEPLOY_PORT = int(sys.argv[2])
    except IndexError:
        ENABLE_DEPLOY = sys.argv[1] == "deploy"

    if ENABLE_DEPLOY:
        print("===\nDeployed on port 80.\n===")
        uvicorn.run(
                "main:app",
                host="0.0.0.0",
                port=80,
                )
    else:
        print(f"===\nRunning on Local Testing environment on port: {DEPLOY_PORT}\n===")
        uvicorn.run(
                "main:app",
                port=DEPLOY_PORT,
                )

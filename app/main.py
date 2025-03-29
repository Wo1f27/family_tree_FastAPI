from fastapi import FastAPI


app = FastAPI()


@app.get('/')
def hello():
    return {'muuuur': 'Hello'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', reload=True)

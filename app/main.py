from fastapi import FastAPI


app = FastAPI()

app.include_router()
app.include_router()


@app.get('/')
def hello():
    return {'title': 'Hello on Family-Tree'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', reload=True)

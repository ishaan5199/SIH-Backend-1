import json
from turtle import down
import uuid
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
import validators
import os
from elasticsearch import helpers

import configs
import utils

client = configs.client
router = APIRouter()

@router.post("/texttoindex")
async def add_data_to_index(data: str):
    data = json.loads(data)
    fetch_index = data.get('index',None)
    if not fetch_index:
        raise HTTPException(status_code=400, detail="Index not found")
    fetch_doc_type = data.get('doc_type',None)
    if not fetch_doc_type:
        raise HTTPException(status_code=400, detail="Doc Type not found")
    if fetch_doc_type == 'text':
        fetch_data = data.get('data',None)
        if not fetch_data:
            raise HTTPException(status_code=400, detail="Data not found")
        try:
            fetch_data['doc_type'] = fetch_doc_type
            client.index(index=fetch_index,body=fetch_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"message":"Data added to index","data":data}
    else:
        raise HTTPException(status_code=400, detail="Doc Type not supported for this endpoint")


@router.post("/pdftoindex")
async def add_pdf_to_index(data:str):
    fetch_url = json.loads(data).get('url',None)
    if not fetch_url:
        raise HTTPException(status_code=400, detail="URL not found")
    if not validators.url(fetch_url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    fetch_index = json.loads(data).get('index',None)
    if not fetch_index:
        raise HTTPException(status_code=400, detail="Index not found")
    fetch_doc_type = json.loads(data).get('doc_type',None)
    if not fetch_doc_type:
        raise HTTPException(status_code=400, detail="Doc Type not found")
    if fetch_doc_type == 'pdf':
        try:
            fetch_path = utils.download_data_from_cloudinary(fetch_url)
        except Exception as e:
            raise HTTPException(status_code=500,detail="Error Downloading File from Cloud on Server " + str(e))
        try:
            content = utils.get_data_from_pdf(fetch_path)
            meta = utils.get_meta_data_from_doc(fetch_path,'pdf')
        except Exception as e:
            os.remove(fetch_path)
            raise HTTPException(status_code=500,detail="Error Fetching Data From PDF " + str(e))
        data = {
        'doctype':fetch_doc_type,
        'meta':meta,
        'content':content,
        'url':fetch_url
        }
        try:
             client.index(index=fetch_index,body=data)
        except Exception as e:
            os.remove(fetch_path)
            raise HTTPException(status_code=500,detail="Error Adding Data to Index " + str(e))
        os.remove(fetch_path)
        return {"message":"Data added to index","data":data}
    
    else:
        raise HTTPException(status_code=400, detail="Doc Type not supported for this endpoint")


@router.post("/wordtoindex")
async def add_word_to_index(data:str):
    fetch_url = json.loads(data).get('url',None)
    if not fetch_url:
        raise HTTPException(status_code=400, detail="URL not found")
    if not validators.url(fetch_url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    fetch_index = json.loads(data).get('index',None)
    if not fetch_index:
        raise HTTPException(status_code=400, detail="Index not found")
    fetch_doc_type = json.loads(data).get('doc_type',None)
    if not fetch_doc_type:
        raise HTTPException(status_code=400, detail="Doc Type not found")
    if fetch_doc_type == 'doc':
        try:
            fetch_path = utils.download_data_from_cloudinary(fetch_url)
        except Exception as e:
            raise HTTPException(status_code=500,detail="Error Downloading File from Cloud on Server " + str(e))
        try:
            content = utils.extract_data_from_doc(fetch_path)
            meta = utils.get_meta_data_from_doc(fetch_path,'doc')
        except Exception as e:
            os.remove(fetch_path)
            raise HTTPException(status_code=500,detail="Error Fetching Data From Doc " + str(e))
        data = {
            'doctype':fetch_doc_type,
            'meta':meta,
            'content':content,
            'url':fetch_url
        }
        try:
             client.index(index=fetch_index,body=data)
        except Exception as e:
            os.remove(fetch_path)
            raise HTTPException(status_code=500,detail="Error Adding Data to Index " + str(e))
        os.remove(fetch_path)
        return {"message":"Data added to index","data":data}
    else:
        raise HTTPException(status_code=400, detail="Doc Type not supported for this endpoint")
        
@router.post("/sqltoindex")
async def add(file: UploadFile= File(...), name: str = Form()):
    try:
        contents = await file.read()
        try:
            f = open('sql.sql', 'wb')
            f.write(contents)
            f.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        path = os.path()
        cmd = f"sqldump-to -i {path}/sql.sql > j.json"
        os.system(cmd)

        def generate_docs():

            try:
                f = open('j.json', encoding='utf8')
                data = json.load(f)
                new_data = data
            except:
                f = open('j.json', encoding='utf8')
                data = f.readlines()
                new_data = []
                for row in data:
                    dict_obj = json.loads(row)
                    new_data.routerend(dict_obj)  

            for row in new_data:
                doc = {
                        "_index": name,
                        "_id": uuid.uuid4(),
                        "_source": row,
                    }
                yield doc
    
        helpers.bulk(client, generate_docs())
        print("Done")
        os.remove('j.json')
        os.remove('sql.sql')        
        return {"status": 1}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
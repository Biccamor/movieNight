from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel('BAAI/bge-m3',  
                       use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

def create_vector(prompt:str):
    
    embedding = model.encode(prompt, 
                            batch_size=20, 
                            max_length=512,
                            normalize_embedding=True
                            )['dense_vecs']
    
    embedding_list = embedding[0].tolist()
    return embedding

def get_recoms(embedding, limit: int = 5) -> list:  
    ...
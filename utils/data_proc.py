import os
import yaml
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger()

def load_xml_to_doc(file_path: str) -> list:
    """
    Load XML file and convert it to a list of documents.
    """
    tree = ET.ElementTree(file=file_path)
    root = tree.getroot()
    documents = []
    # 保存需要跳过的、无content驱动的容器节点
    container_tags = {'GroupBox', 'Pane', 'QWidget', 'Custom', 'Panel'}

    for elem in root.iter():
        if elem.tag not in container_tags and any(attr in elem.attrib for attr in ['title', 'name']):
            text = f"tag: {elem.tag}, title: {elem.attrib.get('title', '')}, name: {elem.attrib.get('name', '')}, class_name: {elem.attrib.get('class_name', '')}, path: {elem.attrib.get('path', '')}"
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "xml_path": file_path,
                        "tag": elem.tag,
                        "name": elem.attrib.get('name', ''),
                    }
                )
            )
    logger.info(f"Loaded {len(documents)} documents from XML file: {file_path}")

    return documents

def load_yaml_to_doc(file_path: str) -> list:
    """
    Load YAML file and convert it to a list of documents.
    """
    def traverse_yaml(obj, prefix="", file_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{prefix}.{key}" if prefix else key
                yield from traverse_yaml(value, current_path, file_path)
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                current_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
                yield from traverse_yaml(item, current_path, file_path)
        else:
            content = f"path: {prefix}\nvalue: {obj}"
            yield Document(
                page_content=content,
                metadata={"yaml_path": file_path, "key_path": prefix}
            )

    with open(file_path, "r", encoding='utf-8') as f:
        data = yaml.safe_load(f)

    logger.info(f"Loaded {len(data)} documents from YAML file: {file_path}")

    return list(traverse_yaml(data, file_path=file_path))

def load_documents_to_chroma(dir_path: str) -> Chroma:
    """
    Load XML and YAML files from the specified directory and store them in a Chroma vector store.
    """
    documents = []
    for root, _, files in os.walk(dir_path): # 递归解析dir_path目录下的所有文件
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.endswith('.xml'):
                documents.extend(load_xml_to_doc(file_path))
            elif file_name.endswith('.yaml'):
                documents.extend(load_yaml_to_doc(file_path))

    if not documents:
        logger.error("No documents found to load.")
        raise Exception("No documents found to load.")

    embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
    db = Chroma.from_documents(
        documents,
        embedding=embeddings,
        persist_directory='./knowledge_base'
    )
    return db


if __name__ == '__main__':
    db = load_documents_to_chroma('../doc')
    retriever = db.as_retriever()
    query = '如何发送消息到文件传输助手？'
    docs = retriever.get_relevant_documents(query)
    print(docs[0].page_content)
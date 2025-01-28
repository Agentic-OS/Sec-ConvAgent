# Sec-ConvAgent

this a project related into Security Conversation over Agent-User to enhance the Privacy-data Driven 

#### the Architecture system design 


```mermaid
graph LR
    U((User)) --> F[Frontend<br>Streamlit]
    F --> E[Encryption<br>Layer]
    E --> B[Backend<br>LangChain]
    B --> V[(Vector DB)]
    B --> D[Decryption<br>Layer]
    D --> O[OLLAMA<br>LLM]
    
    subgraph Container
        F
        E
        B
        D
        V
    end
    
    subgraph External
        O
    end

    classDef container fill:#e1f5fe,stroke:#01579b
    classDef external fill:#fff3e0,stroke:#ff6f00
    classDef user fill:#f5f5f5,stroke:#616161
    classDef security fill:#e8f5e9,stroke:#2e7d32
    
    class F,B,V container
    class O external
    class U user
    class E,D security
```

this project include the following steps :

1. building agent connected with vector Database embedding to store the Conversation History 
2. Decrypting and Encrypting Mechanisms of the conversation between Agent and User 
3. all the conversation being Stored Encryption Level 
4. Retrieval-Augmentation-Generation technique to improve the Agent Response up-to data knowledge 
5. using Genmi Api key Ollama Compatibility 


#### the techno used 

- LangChain 
- langaph 
- Chorma 
- cryptography
- request 

## Secure Chat Application

This is a secure chat application built using Python and various libraries and frameworks, including Streamlit, LangChain, and cryptography. The app provides a conversational interface for users to interact with, while ensuring the security and privacy of user data.

## Features

* Secure conversational interface
* Natural language understanding and response generation
* Personalized experience through vector store management
* Data security through encryption and secure storage
* Access control mechanisms for authorized users

## System Design

The system consists of the following components:

* Frontend: Built using Streamlit, provides a web-based interface for users to interact with the chat application
* Backend: Responsible for handling user input, processing messages, and generating responses using LangChain
* Vector Store: Stores user messages and their corresponding embeddings (vector representations) for personalized experience
* Encryption: Uses cryptography to encrypt and decrypt user messages for secure storage and transmission
* Model: Utilizes a pre-trained language model (OLLAMA) to generate responses to user queries

## Technical Requirements

* Python 3.10 or later
* Streamlit 1.29.0 or later
* LangChain 0.1.0 or later
* Cryptography 41.0.0 or later
* OLLAMA model (deepseek-r1:1.5b)

## Installation

1. Clone the repository
2. Install dependencies using `pip install -r requirements.txt`
3. Run the application using `streamlit run app.py`

## Usage

1. Open a web browser and navigate to `http://localhost:8501`
2. Interact with the chat application by typing messages and receiving responses
3. Use the sidebar to view chat history, model information, and controls

## System Flow

1. User Input: The user types a message and submits it to the frontend.
2. Process User Input: The frontend sends the user input to the backend for processing.
3. Store User Message and Embedding: The backend stores the user message and its corresponding embedding in the vector store.
4. Encrypt User Message: The backend encrypts the user message using cryptography.
5. Decrypt User Message: The backend decrypts the user message using cryptography.
6. Generate Response: The backend uses the model to generate a response to the user query.
7. Response: The backend sends the response to the frontend.
8. Display Response: The frontend displays the response to the user.

## System Components

* Frontend: Streamlit
* Backend: LangChain
* Vector Store: Chroma
* Encryption: Cryptography
* Model: OLLAMA


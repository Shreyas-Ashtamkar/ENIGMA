<img src="assets/images/Enigma_logo.jpeg" style="width:50em">
</img>

# ENIGMA

*Expert Network for Intelligent Guidance and Multi-task Assistance*
ENIGMA is a smart system which uses multiple Expert-of-Domain AIs under the hood to handle various parts of a chat request to make somehthing like one large AI. ( Or one big Artificially Intelligent System )

## Overview

ENIGMA is a cutting-edge solution designed to optimize behavioral interactions by integrating multiple AI models, each specialized for specific tasks. The system combines expert systems to deliver superior performance and user experience.

## Models Used

### 1. phi3 - Summary
**Task:** Summarization and Request Identification

The `phi3` model is responsible for summarizing user requests and determining if they are functional or task-based. It ensures that the core of the user's intent is accurately captured and ready for further processing.

### 2. mistral - Function Calling
**Task:** Function Invocation

The `mistral` model handles the invocation of underlying tools and functions. Once the user's request is identified and summarized, `mistral` efficiently calls the appropriate functions to generate the required response.

### 3. llama3 - Conversation
**Task:** Conversational Interface

The `llama3` model facilitates seamless and natural conversation with users. It ensures that interactions are engaging and that users receive coherent and contextually relevant responses.

## Workflow

1. **User Interaction:** The user initiates a conversation with the system using the CLI-based chat interface.
2. **Request Summarization:** The `phi3` model summarizes the user's request and identifies its nature (task-based or informational).
3. **Function Invocation:** If the request is functional, the `mistral` model calls the necessary underlying tools or functions to process the request.
4. **Response Generation:** The result is then forwarded to the `llama3` model, which constructs a conversational response and delivers it back to the user.
5. **User Feedback:** The user receives a coherent, optimized response, enhancing the overall interaction experience.

## Flow of Code
![Flow of Code - Tech Stack](<assets/images/Flow of Code.png>)

## Parts of System
![Technology Stack](<assets/images/System Diagram.png>)

## Benefits

- **Optimized Interactions:** By leveraging specialized models, the system ensures accurate and efficient handling of user requests.
- **Enhanced User Experience:** Natural and engaging conversations improve user satisfaction and interaction quality.
- **Scalability:** The system's modular design allows for easy scalability and integration of additional models as needed.

## Conclusion

ENIGMA represents a significant advancement in behavioral optimization through expert systems. By combining the strengths of `phi3`, `mistral`, and `llama3`, it provides a robust, efficient, and user-friendly solution for diverse applications.

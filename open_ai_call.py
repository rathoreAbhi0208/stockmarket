"""
OpenAI API Usage Script
This script demonstrates how to use the OpenAI API for various tasks.
Make sure to install the OpenAI library: pip install openai
"""

from openai import OpenAI
import os

# Initialize the OpenAI client
# You can set your API key in one of two ways:
# 1. Set it as an environment variable: export OPENAI_API_KEY='your-key-here'
# 2. Pass it directly (not recommended for production)

client = OpenAI(
    # api_key=os.environ.get("OPENAI_API_KEY")  # Reads from environment variable
    api_key=""
)

def chat_completion_basic():
    """Basic chat completion example"""
    print("=== Basic Chat Completion ===")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4", "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}\n")


def chat_completion_conversation():
    """Example with conversation history"""
    print("=== Conversation with History ===")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's 2+2?"},
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    # Add assistant's response to history
    messages.append({
        "role": "assistant",
        "content": response.choices[0].message.content
    })
    
    print(f"Assistant: {response.choices[0].message.content}")
    
    # Continue the conversation
    messages.append({
        "role": "user",
        "content": "What about multiplying that by 3?"
    })
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    print(f"Assistant: {response.choices[0].message.content}\n")


def streaming_response():
    """Example with streaming response"""
    print("=== Streaming Response ===")
    
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Count from 1 to 5 slowly"}
        ],
        stream=True
    )
    
    print("Response: ", end="")
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")


def function_calling_example():
    """Example using function calling"""
    print("=== Function Calling ===")
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "What's the weather like in Boston?"}
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    message = response.choices[0].message
    if message.tool_calls:
        print(f"Function called: {message.tool_calls[0].function.name}")
        print(f"Arguments: {message.tool_calls[0].function.arguments}\n")
    else:
        print(f"Response: {message.content}\n")


def image_generation():
    """Example of generating images with DALL-E"""
    print("=== Image Generation ===")
    
    response = client.images.generate(
        model="dall-e-3",  # or "dall-e-2"
        prompt="A serene mountain landscape at sunset",
        size="1024x1024",
        quality="standard",
        n=1
    )
    
    image_url = response.data[0].url
    print(f"Generated image URL: {image_url}\n")


def text_to_speech():
    """Example of text-to-speech"""
    print("=== Text to Speech ===")
    
    response = client.audio.speech.create(
        model="tts-1",  # or "tts-1-hd" for higher quality
        voice="alloy",  # alloy, echo, fable, onyx, nova, shimmer
        input="Hello! This is a text to speech example."
    )
    
    # Save to file
    response.stream_to_file("output.mp3")
    print("Audio saved to output.mp3\n")


def embeddings_example():
    """Example of creating embeddings"""
    print("=== Creating Embeddings ===")
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="The quick brown fox jumps over the lazy dog"
    )
    
    embedding = response.data[0].embedding
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}\n")


def main():
    """Run all examples"""
    try:
        chat_completion_basic()
        chat_completion_conversation()
        streaming_response()
        function_calling_example()
        embeddings_example()
        
        # Uncomment these if you want to test them
        # (they create files or cost more)
        # image_generation()
        # text_to_speech()
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Installed OpenAI library: pip install openai")
        print("2. Set your API key: export OPENAI_API_KEY='your-key-here'")


if __name__ == "__main__":
    main()
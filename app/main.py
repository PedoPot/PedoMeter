from fastapi import FastAPI, HTTPException
from ollama import Client
from app.schemas import Message, Conversation, Conversations

app = FastAPI()
model: str = "conversation-evaluator"


@app.post("/compute-score")
async def compute_score(request: Conversations):
    try:
        # Initialize Ollama client
        client = Client()
        # Format conversations for evaluation
        conversation_texts = []
        for i, conv in enumerate(request.conversations):
            conv_text = f"Conversation {i + 1}:\n"
            for msg in conv.messages:
                # Clearly label who is speaking in each message
                role_label = "User" if msg.role == "user" else "AI Assistant" if msg.role == "assistant" else msg.role
                conv_text += f"{role_label}: {msg.content}\n"
            conversation_texts.append(conv_text)

        evaluation_prompt = "\n\n".join(conversation_texts)

        # Call Ollama
        response = client.chat(
            model=model,
            messages=[
                {"role": "user", "content": evaluation_prompt}
            ]
        )

        # Extract the score from the response
        score_text = response["message"]["content"].strip()

        # Try to parse the score as a number between 0 and 1
        try:
            risk_score = float(score_text)

            # Validate the risk score range
            if 0 <= risk_score <= 1:
                return {"risk_score": risk_score}
            else:
                raise ValueError("Score outside valid range (0-1)")

        except ValueError:
            # If the model didn't return just a number, try to extract it
            import re
            score_match = re.search(r'0(\.\d+)?|1(\.0+)?', score_text)
            if score_match:
                risk_score = float(score_match.group(0))
                return {"risk_score": risk_score}
            else:
                raise HTTPException(
                    status_code=422,
                    detail="Could not extract a valid risk score (0-1) from the model's response"
                )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing conversation score: {str(e)}")

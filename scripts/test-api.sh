#!/bin/bash

# API testing script for Smart Research Assistant

set -e

BASE_URL="http://localhost:8000"

echo "🧪 Testing Smart Research Assistant API..."
echo ""

# Test 1: Health Check
echo "1️⃣ Testing health endpoint..."
curl -s "$BASE_URL/health" | jq '.'
echo ""

# Test 2: Upload text document
echo "2️⃣ Uploading sample text document..."
DOC_RESPONSE=$(curl -s -X POST "$BASE_URL/api/documents/upload-text" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text",
    "text": "Machine learning is a subset of AI that enables systems to learn from data. It includes supervised learning, unsupervised learning, and reinforcement learning. Applications include image recognition, natural language processing, and recommendation systems.",
    "title": "Introduction to Machine Learning",
    "author": "Test User"
  }')

echo "$DOC_RESPONSE" | jq '.'
DOC_ID=$(echo "$DOC_RESPONSE" | jq -r '.id')
echo "Document ID: $DOC_ID"
echo ""

# Wait for processing
echo "⏳ Waiting for document to be processed (15 seconds)..."
sleep 15

# Test 3: Check document status
echo "3️⃣ Checking document status..."
curl -s "$BASE_URL/api/documents/$DOC_ID" | jq '.'
echo ""

# Test 4: Ask a question
echo "4️⃣ Asking a question about the document..."
CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the types of machine learning mentioned?",
    "include_sources": true
  }')

echo "$CHAT_RESPONSE" | jq '.'
CONV_ID=$(echo "$CHAT_RESPONSE" | jq -r '.conversation_id')
echo ""

# Test 5: Follow-up question
echo "5️⃣ Asking a follow-up question..."
curl -s -X POST "$BASE_URL/api/chat/ask" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"What are some applications?\",
    \"conversation_id\": \"$CONV_ID\",
    \"include_sources\": true
  }" | jq '.'
echo ""

# Test 6: List conversations
echo "6️⃣ Listing conversations..."
curl -s "$BASE_URL/api/conversations" | jq '.'
echo ""

# Test 7: Get conversation detail
echo "7️⃣ Getting conversation details..."
curl -s "$BASE_URL/api/conversations/$CONV_ID" | jq '.'
echo ""

# Test 8: List all documents
echo "8️⃣ Listing all documents..."
curl -s "$BASE_URL/api/documents" | jq '.'
echo ""

echo "✅ All tests completed!"
echo ""
echo "Note: Make sure to have jq installed for pretty JSON output"
echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"

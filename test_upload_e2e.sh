#!/bin/bash
# End-to-end test for document upload + LLM extraction

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="http://localhost:8000/api/v1"
TEST_PDF="test_judgment.pdf"

echo -e "${YELLOW}Creating test PDF...${NC}"

# Create a minimal valid PDF using reportlab
python3 << 'EOF'
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("test_judgment.pdf", pagesize=letter)
c.setFont("Helvetica", 12)

# Add content
c.drawString(50, 750, "HIGH COURT OF DELHI")
c.drawString(50, 700, "CIVIL APPEAL NO. 2024-001")
c.drawString(50, 650, "Dated: 2024-05-01")
c.drawString(50, 600, "")
c.drawString(50, 550, "PETITIONER: State of Delhi")
c.drawString(50, 500, "RESPONDENT: ABC Corporation")
c.drawString(50, 450, "")
c.drawString(50, 400, "JUDGMENT")
c.drawString(50, 350, "This court hereby directs the respondent to comply with all statutory obligations")
c.drawString(50, 300, "within 30 days of the order. The respondent shall submit a compliance report")
c.drawString(50, 250, "within 45 days. Failure to comply will result in contempt of court proceedings.")
c.drawString(50, 200, "")
c.drawString(50, 150, "Judge Signature")
c.save()
print("✓ test_judgment.pdf created")
EOF

echo -e "${GREEN}✓ Test PDF created${NC}"

# Test 1: Register user
echo -e "\n${YELLOW}[1/5] Registering test user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "${API_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_upload@example.com",
    "password": "TestUpload123!",
    "full_name": "Upload Tester"
  }')

echo "Response: $REGISTER_RESPONSE"

# Test 2: Login
echo -e "\n${YELLOW}[2/5] Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_upload@example.com",
    "password": "TestUpload123!"
  }')

echo "Response: $LOGIN_RESPONSE"

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}✗ Failed to get access token${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Access token: ${ACCESS_TOKEN:0:20}...${NC}"

# Test 3: Upload document
echo -e "\n${YELLOW}[3/5] Uploading PDF...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST "${API_URL}/documents/upload" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -F "file=@${TEST_PDF}")

echo "Response: $UPLOAD_RESPONSE"

DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('document_id', ''))" 2>/dev/null || echo "")

if [ -z "$DOCUMENT_ID" ]; then
  echo -e "${RED}✗ Failed to upload document${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Document uploaded with ID: $DOCUMENT_ID${NC}"

# Test 4: Check document status
echo -e "\n${YELLOW}[4/5] Checking document status...${NC}"
sleep 2

for i in {1..10}; do
  STATUS_RESPONSE=$(curl -s -X GET "${API_URL}/documents/${DOCUMENT_ID}/status" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  
  echo "Status check $i: $STATUS_RESPONSE"
  
  STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing_status', ''))" 2>/dev/null || echo "")
  
  if [ "$STATUS" = "PENDING_REVIEW" ]; then
    echo -e "${GREEN}✓ Document transitioned to PENDING_REVIEW (LLM extraction complete!)${NC}"
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo -e "${RED}✗ Document processing failed${NC}"
    ERROR=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error_message', ''))" 2>/dev/null || echo "")
    echo "Error: $ERROR"
    break
  else
    echo "Current status: $STATUS (waiting...)"
    sleep 2
  fi
done

# Test 5: Check extracted fields
echo -e "\n${YELLOW}[5/5] Checking extracted fields...${NC}"
FIELDS_RESPONSE=$(curl -s -X GET "${API_URL}/documents/${DOCUMENT_ID}/fields" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

echo "Extracted fields: $FIELDS_RESPONSE"

echo -e "\n${GREEN}✓ End-to-end test complete!${NC}"

# Cleanup
rm -f test_judgment.pdf

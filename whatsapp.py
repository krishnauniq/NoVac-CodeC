import requests

url = "https://graph.facebook.com/v20.0/805492612657583/messages"
access_token = "EAAVV3fk6SZBMBQNYxqid6V7eV7w87ZASepVWLncFBch76WpcbPxNSwho7qbZBn3UtEZBCIp6RbiddmVtWagp0Aoad2nQPaoVho7HhCzkKTpu1SorsWRwydyCtSSWUaootVMD3TOxW2FlHGs4IOz1ZCxNwLFOh3xDKS9QerXayk6dXR0TxtBdjtIJk3klKW7pnD9FrvuAVFUi4j1PwcYS758e7byXuc2bCRM2ZCAZBFo9rmH0PqXIvfbTKvmuaHkVReOOCqTBbPkm1XgOswF8RnGRgZDZD"

payload = {
  "messaging_product": "whatsapp",
  "to": "919838271539",
  "type": "text",
  "text": {
    "body": "🚀Well done now starr kuch or "
  }
}

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())

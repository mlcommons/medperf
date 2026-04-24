{
	"subject": {{ toJson .Token.email }},
	"sans": {{ toJson .SANs }},
{{- if typeIs "*rsa.PublicKey" .Insecure.CR.PublicKey }}
  "keyUsage": ["dataEncipherment", "digitalSignature"],
{{- else if typeIs "*ecdsa.PublicKey" .Insecure.CR.PublicKey }}
  "keyUsage": ["digitalSignature"],
{{- else }}
  {{ fail "Key type must be RSA or EC. Try again with --kty=RSA or --kty=EC" }}
{{- end }}
  "extKeyUsage": ["serverAuth", "clientAuth"]
}
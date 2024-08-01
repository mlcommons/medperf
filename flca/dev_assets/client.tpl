{
	"subject": {{ toJson .Token.email }},
	"sans": {{ toJson .SANs }},
{{- if typeIs "*rsa.PublicKey" .Insecure.CR.PublicKey }}
  "keyUsage": ["dataEncipherment", "digitalSignature"],
{{- else }}
  {{ fail "Key type must be RSA. Try again with --kty=RSA" }}
{{- end }}
  "extKeyUsage": ["serverAuth", "clientAuth"]
}
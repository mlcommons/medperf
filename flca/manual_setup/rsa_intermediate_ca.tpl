{
  "subject": {{ toJson .Subject }},
  "issuer": {{ toJson .Subject }},
  "keyUsage": ["certSign", "crlSign"],
  "basicConstraints": {
    "isCA": true,
    "maxPathLen": 0
  }
  {{- if typeIs "*rsa.PublicKey" .Insecure.CR.PublicKey }}
    , "signatureAlgorithm": "SHA256-RSAPSS"
  {{- end }}
}
# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - navigation [ref=e2]:
    - generic [ref=e3]:
      - link "Home" [ref=e4] [cursor=pointer]:
        - /url: /
      - list [ref=e6]:
        - listitem [ref=e7]:
          - link "Login" [ref=e8] [cursor=pointer]:
            - /url: /login
  - main [ref=e11]:
    - generic [ref=e14]:
      - img [ref=e16]
      - heading "This QR code is not valid or has expired." [level=2] [ref=e18]
      - paragraph [ref=e19]: This QR code may have been deactivated or does not exist.
  - contentinfo [ref=e20]:
    - generic [ref=e25]:
      - text: Built on
      - link "Frappe" [ref=e26] [cursor=pointer]:
        - /url: https://frappeframework.com?source=website_footer
```
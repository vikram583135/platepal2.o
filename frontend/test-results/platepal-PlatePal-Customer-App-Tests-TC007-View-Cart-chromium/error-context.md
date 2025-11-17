# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]:
    - heading "Login to PlatePal" [level=3] [ref=e6]
    - paragraph [ref=e7]: Enter your credentials to access your account
  - generic [ref=e9]:
    - generic [ref=e10]: Login failed. Please check your credentials.
    - generic [ref=e11]:
      - generic [ref=e12]: Email
      - textbox "Email" [ref=e13]:
        - /placeholder: you@example.com
        - text: customer@platepal.com
    - generic [ref=e14]:
      - generic [ref=e15]: Password
      - textbox "Password" [ref=e16]:
        - /placeholder: ••••••••
        - text: customer123
    - button "Login" [ref=e17] [cursor=pointer]
    - generic [ref=e18]:
      - generic [ref=e23]: Or continue with
      - generic [ref=e24]:
        - button [ref=e25] [cursor=pointer]:
          - img [ref=e26]
        - button [ref=e31] [cursor=pointer]:
          - img [ref=e32]
        - button [ref=e34] [cursor=pointer]:
          - img [ref=e35]
    - paragraph [ref=e37]:
      - text: Don't have an account?
      - link "Sign up" [ref=e38] [cursor=pointer]:
        - /url: /signup
```
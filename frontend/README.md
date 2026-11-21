# InstaMed web app

Next.js customer app for the InstaMed API. See the **Frontend** section of the root
README for architecture (same-origin `/backend` proxy, httpOnly refresh-token cookie,
generated API types).

```powershell
npm install
npm run dev        # http://localhost:3000, API expected on http://127.0.0.1:8000
npm run check      # lint + typecheck + tests
npm run build
npm run gen:api    # regenerate src/lib/api/schema.ts from the running API
```

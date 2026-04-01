# Kanban Project Manager Frontend

Single-board Kanban MVP built on Next.js with in-memory state management.

## Features

- Fixed 5 columns (Backlog / To Do / In Progress / Review / Done)
- Column rename
- Add/Delete cards with title + details
- Drag and drop cards across columns (`@hello-pangea/dnd`)
- Dummy data on initial load
- No persistence (refresh resets board)

## Setup

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Commands

- `npm run dev` - development server
- `npm run build` - production build
- `npm run test` - Jest unit tests
- `npm run lint` - lint with ESLint

## Implementation

Main implementation: `src/app/page.tsx`.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

# Tutorial: Building a Digital Twin Chatbot & Styling Your Next.js Portfolio

Welcome! If you are new to coding, this tutorial will guide you step-by-step through the process I used to transform your website. We started by updating the site's dark-mode theme, and then built a conversational AI "Digital Twin" capable of answering questions about your resume. 

Let's dive into the technology, the high-level steps, the code, and how we can continue improving it!

---

## 1. Summary of the Technology

To build this feature, we leveraged a few popular frameworks and libraries. Think of these as standard sets of "lego bricks" making our job easier:

1. **Next.js**: The core framework running your website. It handles building both your Frontend (what the user sees) and Backend (the server-side code that keeps API keys secure). 
2. **Tailwind CSS**: A styling toolkit. Instead of writing separate CSS files for every button or layout, Tailwind lets us apply precise styles directly in the code (e.g., `text-blue-500` makes text blue).
3. **Vercel AI SDK**: A powerful library that simplifies chatting with AI models. We used it to handle the complex task of "streaming" text—that typewriter-effect where words appear one by one.
4. **OpenRouter**: An AI platform that acts as a router. Instead of locking into one AI provider (like ChatGPT or Claude), OpenRouter lets us use models like `stepfun/step-3.5-flash:free` through a single interface.

---

## 2. High-Level Walkthrough

Here is the straightforward path we took to integrate these new features:

**Step 1. Theme Upgrade (The Look)**
We opened `app/globals.css`, which holds the website's universal colors, and modified the existing `rgb` values to shift the theme from generic stark-black to a curated, sleek slate-blue palette.

**Step 2. Building the Brain (The API Route)**
We created a secret backend route in Next.js (`app/api/chat/route.ts`) so your visitors' questions could be sent to OpenRouter securely, without exposing your private `OPENROUTER_API_KEY`. 

**Step 3. Building the Body (The Chat Widget)**
We created a new visual component (`components/ui/chat.tsx`) representing the chat bubble. It manages the chat window opening/closing, user input, and displaying the conversational back-and-forth.

**Step 4. Wiring it Together (The Layout)**
A website's "Layout" (`app/layout.tsx`) represents elements that appear on *every* page. By inserting our `<Chat />` widget there, the Digital Twin is accessible globally across your portfolio.

---

## 3. Detailed Code Review

Let's take a look under the hood at the exact code that makes this magic work.

### A. Updating the Theme (`app/globals.css`)
In CSS, variables start with `--`. By updating the exact numeric values of `--bg` (background) and `--card` (floating elements), we instantly changed the look of the entire website.
```css
:root {
  /* We changed the background to a dark slate blue / rgb 15 23 42 */
  --bg: 15 23 42;
  --fg: 248 250 252; /* Lighter slate color for readable text */

  /* And used a striking sky blue for our accents! */
  --accent: 56 189 248;
}
```

### B. The Secret "API Endpoint" (`app/api/chat/route.ts`)
This file is the backend server logic. Let's break down how the AI is customized to act as *you*. 

```typescript
// 1. We import the AI SDK tools and your resume data directly!
import { createOpenAI } from '@ai-sdk/openai';
import { streamText } from 'ai';
import { profile } from '@/lib/profile';

// 2. We set up our connection to OpenRouter
const openrouter = createOpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY, 
});

export async function POST(req: Request) {
  try {
    // 3. We read the message that the user typed in the browser
    const text = await req.text();
    const { messages } = JSON.parse(text);

    // 4. We build the "System Prompt" (The robot's rulebook).
    // It injects your actual profile.name, and profile.experience automatically!
    const systemPrompt = `You are the AI Digital Twin of ${profile.name}.
    Your job is to answer questions about ${profile.name}'s career...
    Experience: ${profile.experience.map(e => e.role).join(", ")}`;

    // 5. We ask the AI to generate a response, and importantly, 'await' it to finish processing.
    const result = await streamText({
      model: openrouter('stepfun/step-3.5-flash:free') as any,
      system: systemPrompt,
      messages,
    });

    // 6. We beam the text back to the browser piece by piece (streaming)
    return result.toDataStreamResponse();
  } catch (error) {
    return new Response("Error processing chat request", { status: 500 });
  }
}
```

### C. The Frontend Component (`components/ui/chat.tsx`)
This is the visual chat widget. It uses a Next.js/React standard called "Hooks" (functions that start with `use`).

```tsx
"use client"; // This tells Next.js this code runs in the user's browser
import { useChat } from "ai/react";

export function Chat() {
  // `isOpen` keeps track of whether the chat window is currently popped up
  const [isOpen, setIsOpen] = useState(false);
  
  // `useChat` does the heavy lifting! It gives us the chat history (`messages`)
  // and magically takes care of calling our API route when the user presses Send.
  const { messages, input, handleInputChange, handleSubmit } = useChat();

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {isOpen ? (
        <div className="chat-window">
          {/* Loop over our list of messages and display each one */}
          {messages.map((m) => (
            <div key={m.id}>
              {m.role === "user" ? "Visitor: " : "Twin: "}
              {m.content}
            </div>
          ))}
          
          {/* A standard HTML form for the chat input box */}
          <form onSubmit={handleSubmit}>
            <input value={input} onChange={handleInputChange} />
          </form>
        </div>
      ) : (
        // The standard Floating Button that users click to open the chat
        <button onClick={() => setIsOpen(true)}>Open Chat</button>
      )}
    </div>
  );
}
```

---

## 4. How the Code Can Be Improved (Self-Review)

While the implementation works great, a hallmark of excellent engineering is constantly analyzing how to improve. Here are 5 ways this code could be enhanced:

1. **Implement API Rate Limiting**: 
   Right now, anyone on the internet can continually spam messages to your API route, which could drain your OpenRouter credits. We should add a standard Rate Limiter (e.g., maximum 20 messages per IP address per hour).
2. **Graceful Error Handling UI**: 
   If OpenRouter is down, the code catches it internally and logs a 500 error. However, we should surface a clean, user-friendly "Toast" popup in the UI that politely says *"My digital twin is currently sleeping, try again later!"* rather than freezing.
3. **Retrieval-Augmented Generation (RAG)**: 
   Presently, we inject your *entire* resume directly into the System Prompt. If your resume gets massively large, it could hit AI context limits. A better approach would be vectorizing your resume in a database and only feeding the AI the paragraphs relevant to the user's specific question.
4. **Fix Strict Types & Versioning**: 
   In `app/api/chat/route.ts`, we used the `as any` statement (`openrouter(...) as any`) to silence a conflict between differing library versions. Although functionally perfectly fine, it's a "code smell" in TypeScript. We should use rigid interface matching by unifying the AI SDK package typings.
5. **Mobile-Specific Chat Layout**: 
   The chat window is hardcoded to a fixed width block (`w-[350px]`). On smaller phones, it might overflow or look cramped. We could enhance it using CSS container queries so it takes up `100vw` (the entire screen width) uniquely on mobile devices for easier reading.

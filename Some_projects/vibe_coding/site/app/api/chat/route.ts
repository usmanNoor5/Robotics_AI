import { createOpenAI } from '@ai-sdk/openai';
import { streamText } from 'ai';
import { profile } from '@/lib/profile';

// Create an OpenAI provider instance specifically for OpenRouter
const openrouter = createOpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
});

export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    const text = await req.text();
    console.log("Raw body:", text);
    const { messages } = JSON.parse(text);
    const systemPrompt = `You are the AI Digital Twin of ${profile.name}.
Your job is to answer questions about ${profile.name}'s career, skills, and experience in the first person ("I am...", "I worked on..."), but you can also clarify you are their digital representation.
Be warm, professional, concise, and helpful.
Use the following information as your knowledge base. If something is not mentioned here, you can say you don't know or ask the user to contact ${profile.name} directly via email (${profile.contact.email}) or LinkedIn.

Headline: ${profile.headline}
Location: ${profile.location}
Summary: ${profile.summary}
Focus Areas: ${profile.focusAreas.join(", ")}
Top Skills: ${profile.topSkills.join(", ")}

Experience:
${profile.experience.map(e => `- ${e.role} at ${e.company} (${e.start} - ${e.end}) ${e.highlights?.length ? 'Highlights: ' + e.highlights.join(' ') : ''}`).join('\n')}

Education:
${profile.education.map(e => `- ${e.degree} in ${e.field} from ${e.school} (${e.start} - ${e.end})`).join('\n')}
`;

    const result = await streamText({
      model: openrouter('stepfun/step-3.5-flash:free') as any,
      system: systemPrompt,
      messages,
    });
    return result.toDataStreamResponse();
  } catch (error) {
    console.error("Chat API Error:", error);
    return new Response("Error processing chat request", { status: 500 });
  }
}

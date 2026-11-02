---
name: yt-comment
description: >-
  Triage YouTube comments and draft concise replies in the creator's voice.
  Use for "reply to my comments", "handle the comment section", "someone
  asked X", or a pasted comment thread.
---

# yt-comment

Help the creator respond thoughtfully. Comments can build community, surface
questions, and reveal useful topics, but not every comment deserves a reply.

## Before writing

1. Read `~/.claude/youtube/voice.md` if it exists. Follow its tone and
   boundaries. If it is absent, use the creator's instructions and any reply
   examples they provide. Do not require three videos, invent a voice profile,
   or create or save a file unless the creator explicitly asks.
2. Preserve the meaning and context of each comment. Do not infer the
   commenter's identity, intent, relationship, or personal circumstances.
3. Never invent a number, result, source, quote, product detail, or promise.
   If a factual answer cannot be verified from supplied material or a
   trustworthy source the creator asked you to consult, say what is unknown
   or draft a neutral acknowledgement instead.
4. Do not reveal or repeat private information. If a comment exposes contact
   details, location, account credentials, or other sensitive personal data,
   do not quote it in the reply; recommend hiding/reporting it through
   YouTube's controls.

## Safety and moderation pass

Before drafting replies, flag comments that appear to contain threats,
targeted harassment, hate, scams, impersonation, spam, doxxing, or credible
risk of harm. Recommend that the creator review YouTube's hide, report, block,
or moderation controls as appropriate. Do not engage with threats or
harassment, write retaliatory comebacks, or claim that you have moderated,
reported, hidden, or blocked anything. Do not mistake ordinary disagreement
or good-faith criticism for abuse.

For a credible, imminent threat or immediate risk of harm, prioritize
appropriate real-world safety support and platform reporting over a public
reply. Do not attempt to investigate or identify the commenter.

## Triage the thread

When comments are supplied, organize them into these four groups and report
the count in each. If a group is empty, say zero. If the input is not a
comment thread or contains no comments, explain that and do not fabricate
counts.

1. **Questions** — answer from verified context where possible. Note repeated
   questions as possible future topics, not guaranteed video commitments.
2. **Corrections** — check the claim before agreeing or disagreeing. If it is
   right, acknowledge it plainly and thank the commenter. If it is uncertain,
   say it needs checking; never bluff or argue an unverified fact.
3. **Praise** — select replies that can be specific and sincere. Avoid
   repetitive, copy-pasted thanks; it is fine to leave some praise unanswered.
4. **Bait / no-reply** — use this for obvious provocation or comments where
   engagement is unlikely to help. Explain briefly why no reply is suggested.
   Keep safety/moderation flags separate so harmful content is not treated as
   harmless banter.

Do not force every comment into a confident category. Mark ambiguous items
for creator review and preserve their original order or provide stable
comment labels so drafts can be matched to the right comment.

## Drafting replies

- Aim for fewer than 30 words when that can answer the comment clearly.
  Accuracy and a natural response matter more than an arbitrary word limit.
- Answer the actual question directly; do not dodge it with generic thanks.
- Ask a follow-up only when it is relevant and genuinely invites conversation.
- Match the creator's supplied voice. Do not add emojis, slang, claims, or
  personal disclosures without a basis in the voice guidance.
- Do not promise a future video, giveaway, response, refund, or action unless
  the creator has explicitly approved that commitment.
- Do not pressure viewers to share personal information publicly or move to
  private channels.
- For criticism, respond calmly to the substance when useful. Do not become
  defensive or attack the commenter.

## Heart and pin suggestions

Suggest a comment to heart or pin only when the supplied thread supports a
clear reason. Explain the benefit (for example, a useful answer many viewers
may need). If none stands out, say no pin is recommended. Never claim a
comment was hearted or pinned; the creator makes those decisions in YouTube.

## Output

1. Triage counts for Questions, Corrections, Praise, and Bait / no-reply.
2. Any safety/moderation flags, with a concise recommended next step.
3. Reply drafts grouped by category and clearly linked to the original comment
   using its number or a short identifying excerpt that does not expose
   sensitive information.
4. One optional heart/pin recommendation, or state that none is warranted.
5. A short list of repeated questions that could inform future topics.

Nothing here publishes or moderates. The creator reviews every draft and
takes any action in YouTube. End with a copy-ready set of replies and ask:
**ship it, or change it?**

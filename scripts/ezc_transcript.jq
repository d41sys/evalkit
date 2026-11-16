# Render one ezc session transcript (JSONL) as Markdown for reading:
#   jq -r -f scripts/ezc_transcript.jq case.jsonl > case.md
# Shows user/assistant text, tool calls, tool results (data only) and the harness flags; hides thinking.
if .type == "message" then
  .message as $m
  | ($m.content | if type == "string" then [{type: "text", text: .}] else . end)[]
  | if $m.role == "toolResult" then
      # strip the injection-guard preamble, keep the tool's JSON
      "**tool result** `\($m.toolName)`:\n```json\n\(.text // "" | sub("(?s)^.*<tool_data[^>]*>\\s*"; "") | sub("(?s)\\s*</tool_data>.*$"; ""))\n```\n"
    elif .type == "toolCall" then "**tool call** `\(.name)` `\(.arguments | tostring)`\n"
    elif .type == "text" then "**\($m.role)**: \(.text)\n"
    else empty end
elif .type == "custom" and .customType != "tool_approval" then
  "> harness: `\(.customType)` \(.data | tostring)\n"
else empty end

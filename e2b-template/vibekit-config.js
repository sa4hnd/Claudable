// VibeKit configuration for custom E2B sandbox template
// This file shows how to configure VibeKit to use the new custom template

const e2bProvider = createE2BProvider({
  apiKey: process.env.E2B_API_KEY,
  templateId: "your-new-template-id" // Replace with actual template ID after building
});

const vibeKit = new VibeKit()
  .withAgent({
    type: "claude",
    provider: "anthropic",
    apiKey: process.env.ANTHROPIC_API_KEY,
    model: "claude-sonnet-4-20250514",
  })
  .withSandbox(e2bProvider);

// Resource specifications for the custom template
const sandboxConfig = {
  cpu: 2,
  memory: "4GB",
  templateId: "your-new-template-id"
};

// Example usage in your VibeKit bridge
export { e2bProvider, vibeKit, sandboxConfig };

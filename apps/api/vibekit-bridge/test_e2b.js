const { createE2BProvider } = require('@vibe-kit/e2b');

console.log('Testing E2B provider creation...');

try {
  const e2bProvider = createE2BProvider({
    apiKey: "e2b_014ebb12b54a1e197e59b99c0002cdb88a79cd38",
    templateId: "vibekit-claude"
  });
  console.log('✅ E2B provider created successfully');
} catch (error) {
  console.error('❌ Error creating E2B provider:', error.message);
}

// Test with environment variable
process.env.E2B_API_KEY = "e2b_014ebb12b54a1e197e59b99c0002cdb88a79cd38";

try {
  const e2bProvider2 = createE2BProvider({
    apiKey: process.env.E2B_API_KEY,
    templateId: "vibekit-claude"
  });
  console.log('✅ E2B provider with env var created successfully');
} catch (error) {
  console.error('❌ Error creating E2B provider with env var:', error.message);
}

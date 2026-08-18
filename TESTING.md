# Reoteab v0.1.0-beta.1

This is an early testing build based on Coteab v2.2.0.

### Fixes being tested

1. Merchant settings

   * Invalid or blank merchant settings should no longer cause the merchant handler to abort.
   * Test Mari and Jester normally.
   * If possible, test a previously problematic merchant configuration.

2. Fishing + merchant failsafe

   * Merchant automation should no longer cause the 60-second fishing failsafe to trigger simply because the merchant sequence took too long.
   * Fishing failsafe should still work normally outside merchant automation.

3. Biome webhooks

   * Rare biome start webhooks should no longer be overtaken by end webhooks.
   * Verify start/end ordering.
   * Watch for duplicate or missing biome messages.

### When reporting a bug

Please provide:

* What you were doing
* What you expected
* What happened instead
* Screenshot/video if useful
* `error_logs.txt` if an error occurred
* Whether the issue also happened in Coteab v2.2.0

Do not publicly post webhook URLs, private server links, tokens, or other private configuration.

To get started, create an .env file, with this in it.
You need to generate your own vapid keys, google that.

# Copy to .env and fill in as you enable real Web Push.
# Generate keys (any machine with node installed):
#   npx web-push generate-vapid-keys --json
#
# Then paste:
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_SUBJECT=mailto:admin@test.net

# Optional
PUSH_QUEUE_KEY=taskflow:push:queue

After saving the env file, you can docker compose up, and it should build the scheduler.
The default user (root) will be generated on first launch. The password is located data folder, called "bootstrap_superadmin".

Features include freedom to bend the platform to your favor, You can set up companies under the admin menu,
Features include the freedom to bend the platform to your favor.

From the Admin menu, you can:
Create and manage companies
Control which users can see which companies
Enable or disable notifications
Adjust how tasks are grouped and displayed
There are no dropdown previews for tasks.
You must explicitly open a company to see its tasks — this is intentional and keeps things HIPAA-safe.

Tasks & workflow
Tasks are tied to companies, not users.

You can:
Create tasks per company
Assign categories and priorities
Mark tasks complete when finished
Hide completed tasks to keep things clean


Notifications
Browser notifications are supported if the user allows them.

They:
Tell you when tasks are waiting
Mention the company (never patients)
Don’t leak task details
Can be tested with the Test notify button
If notifications don’t fire, check browser permissions first. It’s almost always that.

Themes
Light and dark mode are both supported.
Theme choice is stored locally in the browser.
Dark mode uses neutral grays instead of neon blues so your eyes don’t melt after 10 hours.

Final notes
This project assumes:
You know what Docker is
You’re comfortable editing env files
You don’t want a bloated SaaS telling you how to run your own shit

If something breaks, check the logs.
If it still breaks, it’s probably your env file.
and if it still breaks, dont bother me. 

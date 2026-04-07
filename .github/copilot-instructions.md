# Copilot Instructions

## Design Context

### Users
- Primary users are Chinese-speaking people who care about eating well but may not know what diet fits their body condition, goals, or budget.
- The product should support multiple real-life scenarios: daily meal decisions, fitness and fat-loss planning, household grocery planning, and special health-management needs.
- Typical usage happens on mobile during short planning windows such as deciding what to eat today, planning a grocery run, or checking whether a plan still fits current constraints.
- Primary job to be done: users should be able to describe their body condition, dietary goals, constraints, and spending level, then quickly receive a practical and trustworthy meal plan without needing nutrition expertise.

### Usage Context
- The shortest successful path is `登录/注册 -> 资料补全 -> 对话 intake -> 查看结果 -> 继续/复用`.
- First-time users should be able to start with minimal personal data, then fill in sensitive body metrics only when the planner needs them.
- Returning users should immediately see whether they can continue, reuse a prior setup, or fix a missing prerequisite.

### Brand Personality
- Professional, trustworthy, caring.
- The interface should feel efficient and expert-led, while still giving users enough warmth and guidance to feel supported rather than judged.
- Copy should sound grounded and useful: explain what matters, what the system already knows, and what the user should do next.

### Aesthetic Direction
- Product direction is light-toned, elegant, and mobile-first, with a grounded consumer-product feel rather than a dashboard or AI-demo feel.
- Move away from the current green-heavy brand impression. Prefer refined neutral surfaces with restrained, tasteful accents that feel closer to premium consumer hardware than health-app cliches.
- Support both light mode and dark mode. Light mode should feel primary and polished; dark mode should feel equally intentional rather than an afterthought.
- Visual emphasis should come from hierarchy, spacing, typography, and state clarity rather than novelty effects or decorative product chrome.

### Aha Moment
- The product becomes convincing when a user sees that the system understands their goal, budget, and missing inputs, then turns that into a concrete budget-safe daily plan with an obvious next step.

### Anti-References
- Do not make this feel like an AI demo, a speculative startup landing page, or a dashboard full of equal-priority cards.
- Avoid fake affordances, hover-only actions, decorative product jargon, and mixed-brand chrome.
- Avoid language that celebrates the system more than the user outcome, including generic "Powered by AI" framing in primary product surfaces.
- Avoid visual directions that feel like generic admin systems, loud wellness branding, or overly saturated health-product palettes.

### Design Principles
1. Truth before flourish: every CTA and status must match real behavior.
2. One dominant next action: each screen should make the next useful step obvious within seconds.
3. Explain missing information: tell users what is missing, why it matters, and how to resolve it.
4. Professional clarity over wellness cliche: use elegant, product-grade visual language instead of heavy health-app green or generic dashboard styling.
5. Lower cognitive load: remove redundant choices, duplicate actions, and decorative framing that does not help a real user finish a meal-planning task.
6. Mobile-safe by default: no critical hover behavior, no horizontal overflow, and touch targets sized for phones.
7. Design both themes on purpose: every major surface should have a considered light and dark treatment.

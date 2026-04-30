# Copilot Instructions

## Design Context

### Users
- Primary users are Chinese-speaking people who care about eating well but may not know what diet fits their body condition, goals, or budget.
- The product supports multiple real-life scenarios: daily meal decisions, fitness and fat-loss planning, household grocery planning, and special health-management needs.
- Typical usage happens on mobile during short planning windows such as deciding what to eat today, planning a grocery run, or checking whether a plan still fits current constraints.
- Primary job to be done: users describe their body condition, dietary goals, constraints, and spending level, then quickly receive a practical and trustworthy meal plan without needing nutrition expertise.

### Usage Context
- Shortest successful path: `登录/注册 -> 资料补全 -> 对话 intake -> 查看结果 -> 继续/复用`.
- First-time users start with minimal personal data; sensitive body metrics are requested only when the planner needs them.
- Returning users immediately see whether they can continue, reuse a prior setup, or fix a missing prerequisite.

### Brand Personality
- Professional, trustworthy, caring.
- Three-word personality: refined, reliable, warm.
- The interface feels efficient and expert-led, with warmth and guidance — supported, not judged.
- Copy is grounded and useful: explain what matters, what the system knows, and what the user should do next.

### Aesthetic Direction
- Premium minimal. Think Notion, Linear, Apple Notes — quiet confidence, no decoration.
- Refined neutral surfaces (warm off-white, warm near-black text) with a single restrained warm amber accent.
- Accent appears ONLY on interactive elements (buttons, links, focus rings) and key CTAs — never on decorative surfaces.
- Visual emphasis comes from hierarchy, spacing, typography, and state clarity — not color saturation, gradients, or shadows.
- Both light and dark mode are intentional. Light mode is primary; dark mode is equally considered.
- Design tokens use oklch for perceptual uniformity, all tinted warm (hue 75).

### Aha Moment
- The product becomes convincing when a user sees that the system understands their goal, budget, and missing inputs, then turns that into a concrete budget-safe daily plan with an obvious next step.

### Anti-References
- NOT an AI demo, speculative startup landing page, or dashboard of equal-priority cards.
- NOT generic admin systems (Element Plus defaults), loud wellness branding, or overly saturated health-app palettes.
- NO gradient text, glassmorphism, neon accents, cyan-on-dark, or purple-to-blue gradients.
- NO identical card grids, hero metric layouts, or icon-above-every-heading templates.
- NO pure black (#000) or pure white (#fff) on large surfaces — always tinted warm.
- NO bounce or elastic easing.

### Design Principles
1. Truth before flourish: every CTA and status must match real behavior.
2. One dominant next action: each screen makes the next useful step obvious within seconds.
3. Explain missing information: tell users what is missing, why it matters, and how to resolve it.
4. Professional clarity over wellness cliche: elegant, product-grade visual language — not health-app green or generic dashboard styling.
5. Lower cognitive load: remove redundant choices, duplicate actions, and decorative framing that does not help a real user finish a meal-planning task.
6. Mobile-safe by default: no critical hover behavior, no horizontal overflow, touch targets sized for phones.
7. Design both themes on purpose: every major surface has a considered light and dark treatment.
8. Restrained accent: one accent color, used only on interactive elements — never on decorative surfaces.
9. Hierarchy through typography and spacing: not through color saturation, gradients, or shadows.

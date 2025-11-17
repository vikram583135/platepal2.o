# PlatePal Style Guide

## Design System

### Colors

- **Primary**: Blue (#3b82f6) - Used for primary actions, links, and brand elements
- **Accent**: Orange (#f97316) - Used for highlights and special elements
- **Success**: Green (#10b981) - Used for success states
- **Error**: Red (#ef4444) - Used for errors and destructive actions
- **Warning**: Amber (#f59e0b) - Used for warnings

### Typography

- **Font Family**: Inter (system fallback)
- **Headings**: Use font-semibold or font-bold
- **Body**: Use font-normal (400)
- **Sizes**: Follow Tailwind's text scale (text-sm, text-base, text-lg, etc.)

### Spacing

- Use Tailwind's spacing scale (4px base unit)
- Common spacing: p-4 (16px), p-6 (24px), gap-4 (16px), gap-6 (24px)

### Components

#### Button

```tsx
<Button variant="default" size="default">Click me</Button>
<Button variant="outline" size="sm">Small</Button>
<Button variant="destructive">Delete</Button>
```

Variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`
Sizes: `default`, `sm`, `lg`, `icon`

#### Card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

#### Input

```tsx
<Input type="email" placeholder="Email" />
```

#### Badge

```tsx
<Badge variant="default">Status</Badge>
```

### Accessibility

- Use semantic HTML elements
- Include ARIA labels where needed
- Ensure keyboard navigation works
- Maintain WCAG AA contrast ratios
- Use focus indicators

### Responsive Design

- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Use Tailwind's responsive prefixes (sm:, md:, lg:)

### Code Style

- Use TypeScript for type safety
- Follow React best practices (hooks, functional components)
- Use meaningful variable and function names
- Keep components small and focused
- Extract reusable logic into custom hooks


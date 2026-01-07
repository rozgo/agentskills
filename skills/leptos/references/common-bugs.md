# Common Bugs and Solutions

## Table of Contents
- [Reactive Lists](#reactive-lists)
- [Reactivity Issues](#reactivity-issues)
- [DOM and Templates](#dom-and-templates)
- [Hydration Problems](#hydration-problems)
- [Build Configuration](#build-configuration)
- [Server Functions](#server-functions)

## Reactive Lists

### Entire list redraws when one item changes

**Problem**: Using plain structs in `RwSignal<Vec<T>>` causes full list re-render.

```rust
// BAD - plain struct, no internal reactivity
struct Todo { id: usize, title: String, completed: bool }
let todos = RwSignal::new(Vec::<Todo>::new());

// Every update redraws ALL items
<For each=move || todos.get() key=|t| t.id let:todo>
    <li>{todo.title}</li>
</For>
```

**Solution A: Signals inside the struct**

```rust
#[derive(Clone)]
struct Todo {
    id: Uuid,                       // Non-reactive ID for keying
    title: RwSignal<String>,        // Reactive!
    completed: RwSignal<bool>,      // Reactive!
}

impl Todo {
    fn new(title: String) -> Self {
        Self {
            id: Uuid::new_v4(),
            title: RwSignal::new(title),
            completed: RwSignal::new(false),
        }
    }
}

<For each=move || todos.get() key=|todo| todo.id let:todo>
    <TodoRow todo />
</For>

#[component]
fn TodoRow(todo: Todo) -> impl IntoView {
    view! {
        <li class:done=move || todo.completed.get()>
            {move || todo.title.get()}
            <button on:click=move |_| todo.completed.update(|c| *c = !*c)>
                "Toggle"
            </button>
        </li>
    }
}
```

**Solution B: Use a Store**

```rust
use reactive_stores::{Store, Field};

#[derive(Clone, Store)]
struct AppState {
    #[store(key: usize = |todo| todo.id)]
    todos: Vec<Todo>,
}

#[derive(Clone, Store)]
struct Todo { id: usize, title: String, completed: bool }

let store = Store::new(initial_state);

<For each=move || store.todos() key=|todo| todo.id().get() let:todo>
    <TodoRow todo />
</For>

#[component]
fn TodoRow(#[prop(into)] todo: Field<Todo>) -> impl IntoView {
    view! {
        <li>{move || todo.title().get()}</li>
    }
}
```

### Static values in For loop

**Problem**: Reading values directly instead of through closures.

```rust
// BAD - captured once, never updates
<For each=move || todos.get() key=|t| t.id let:todo>
    <li>{todo.title.get()}</li>  // Captured at iteration time!
</For>

// GOOD - reactive
<For each=move || todos.get() key=|t| t.id let:todo>
    <li>{move || todo.title.get()}</li>
</For>
```

### Unstable keys

**Problem**: Using index or non-unique values as keys.

```rust
// BAD - index changes when list reorders
<For each=move || items.get().into_iter().enumerate() key=|(i, _)| *i ...>

// GOOD - stable unique ID
<For each=move || items.get() key=|item| item.id ...>
```

## Reactivity Issues

### Writing to signals from effects

**Problem**: Creating chains of signal updates that can cause infinite loops or inefficient updates.

```rust
// BAD - creates update chain
let (a, set_a) = signal(0);
let (b, set_b) = signal(false);

Effect::new(move |_| {
    if a.get() > 5 {
        set_b.set(true);  // Writing inside effect!
    }
});
```

**Solution**: Derive what can be derived.

```rust
// GOOD - derived value
let (a, set_a) = signal(0);
let b = move || a.get() > 5;  // Derived, not stored

// Or use a memo if you need caching
let b = Memo::new(move |_| a.get() > 5);
```

### Nested signal updates causing panic

**Problem**: Updating a signal inside another signal's update callback triggers re-reads.

```rust
// BAD - can panic
let resources = RwSignal::new(HashMap::new());

let update = move |id: usize| {
    resources.update(|resources| {
        resources
            .entry(id)
            .or_insert_with(|| RwSignal::new(0))
            .update(|amount| *amount += 1)  // Nested update!
    })
};
```

**Solution**: Use `batch()` to delay effects.

```rust
// GOOD - batch delays nested effects
let update = move |id: usize| {
    batch(move || {
        resources.update(|resources| {
            resources
                .entry(id)
                .or_insert_with(|| RwSignal::new(0))
                .update(|amount| *amount += 1)
        })
    });
};
```

### Signal not updating view

**Problem**: Reading signal outside reactive context.

```rust
// BAD - value captured once, never updates
let count = RwSignal::new(0);
let text = format!("Count: {}", count.get());  // Captured immediately

view! {
    <p>{text}</p>  // Static, never updates
}
```

**Solution**: Read inside closure for reactivity.

```rust
// GOOD - reactive
let count = RwSignal::new(0);

view! {
    <p>{move || format!("Count: {}", count.get())}</p>
}

// Or just the signal directly
view! {
    <p>"Count: " {count}</p>
}
```

### Effect running too often

**Problem**: Effect tracks dependencies you didn't intend.

```rust
// BAD - effect runs when EITHER signal changes
Effect::new(move |_| {
    let a = signal_a.get();
    let b = signal_b.get();  // Maybe you only wanted to track a?
    expensive_operation(a, b);
});
```

**Solution**: Use `get_untracked()` for non-dependencies.

```rust
// GOOD - only tracks signal_a
Effect::new(move |_| {
    let a = signal_a.get();
    let b = signal_b.get_untracked();  // Not tracked
    expensive_operation(a, b);
});
```

## DOM and Templates

### Input value not updating

**Problem**: Using `value` attribute instead of `prop:value`.

```rust
// BAD - only sets default, doesn't update reactively
let (name, set_name) = signal("".to_string());
view! {
    <input value=name on:input=move |ev| set_name.set(event_target_value(&ev)) />
}
```

**Solution**: Use `prop:value` for reactive binding.

```rust
// GOOD - property binding updates reactively
let (name, set_name) = signal("".to_string());
view! {
    <input
        prop:value=name
        on:input:target=move |ev| set_name.set(ev.target().value())
    />
}
```

This applies to other input properties too:
- `prop:checked` for checkboxes
- `prop:selected` for select options
- `prop:value` for textareas

### Unstable keys in For

**Problem**: Using index or non-stable values as keys.

```rust
// BAD - index changes when list reorders
<For
    each=move || items.get()
    key=|(_idx, item)| _idx  // Index is not stable!
    children=|item| view! { <li>{item}</li> }
/>

// BAD - derived value may not be unique
<For
    each=move || items.get()
    key=|item| item.name.clone()  // Names might duplicate
    children=|item| view! { <li>{item}</li> }
/>
```

**Solution**: Use stable, unique identifiers.

```rust
// GOOD - use actual unique IDs
<For
    each=move || items.get()
    key=|item| item.id  // Stable unique identifier
    let:item
>
    <li>{item.name}</li>
</For>
```

### Component not re-rendering

**Problem**: Props aren't reactive.

```rust
// BAD - value captured once
#[component]
fn Display(value: i32) -> impl IntoView {
    view! { <p>{value}</p> }  // Static after first render
}

let count = RwSignal::new(0);
view! { <Display value=count.get() /> }  // Passes snapshot
```

**Solution**: Pass signals or closures for reactivity.

```rust
// GOOD - pass signal
#[component]
fn Display(value: RwSignal<i32>) -> impl IntoView {
    view! { <p>{move || value.get()}</p> }
}

// Or use into for flexibility
#[component]
fn Display(#[prop(into)] value: Signal<i32>) -> impl IntoView {
    view! { <p>{move || value.get()}</p> }
}
```

## Hydration Problems

### Hydration mismatch warnings

**Problem**: Server HTML differs from client-rendered HTML.

Common causes:
1. Random/timestamp values during SSR
2. Different code paths on server vs client
3. Non-deterministic iteration order

```rust
// BAD - different on each render
view! {
    <div id={format!("id-{}", rand::random::<u32>())}>
        "Content"
    </div>
}
```

**Solution**: Ensure deterministic rendering.

```rust
// GOOD - deterministic ID
let id = use_context::<RequestId>().map(|r| r.0).unwrap_or(0);
view! {
    <div id={format!("id-{}", id)}>
        "Content"
    </div>
}

// Or client-only randomness
#[cfg(feature = "hydrate")]
let id = rand::random::<u32>();
#[cfg(not(feature = "hydrate"))]
let id = 0;
```

### Client-only code running on server

**Problem**: Browser APIs called during SSR.

```rust
// BAD - window doesn't exist on server
let width = window().inner_width();  // Panics on server!
```

**Solution**: Guard with cfg or checks.

```rust
// GOOD - cfg guard
#[cfg(target_arch = "wasm32")]
let width = window().inner_width();
#[cfg(not(target_arch = "wasm32"))]
let width = 0;

// Or runtime check
let width = if cfg!(target_arch = "wasm32") {
    window().inner_width().unwrap_or(0)
} else {
    0
};

// Or use Effect (only runs on client)
let width = RwSignal::new(0);
Effect::new(move |_| {
    if let Some(w) = window().inner_width().ok() {
        width.set(w);
    }
});
```

## Build Configuration

### Cargo feature resolution in workspaces

**Problem**: Pre-2021 resolver causes non-WASM code in WASM builds. Symptom: `mio` fails to build.

```toml
# BAD - workspace without resolver
[workspace]
members = ["app", "server"]
```

**Solution**: Set resolver version.

```toml
# GOOD - explicit resolver
[workspace]
members = ["app", "server"]
resolver = "2"
```

### Conflicting feature flags

**Problem**: Enabling mutually exclusive features.

```toml
# BAD - ssr and csr together
[features]
default = ["ssr", "csr"]  # These conflict!
```

**Solution**: Use separate builds or cfg.

```toml
# GOOD - separate features
[features]
ssr = ["leptos/ssr"]
hydrate = ["leptos/hydrate"]
csr = ["leptos/csr"]
# Only enable one at build time
```

### Missing cfg guards

**Problem**: Server code compiled for client or vice versa.

```rust
// BAD - db code in client bundle
#[server]
async fn get_data() -> Result<Data, ServerFnError> {
    use sqlx::*;  // This shouldn't be in client!
    // ...
}
```

**Solution**: Guard server-only imports.

```rust
// GOOD - guarded imports
#[server]
async fn get_data() -> Result<Data, ServerFnError> {
    #[cfg(feature = "ssr")]
    {
        use sqlx::*;
        // ...
    }
    #[cfg(not(feature = "ssr"))]
    unreachable!()
}

// Or in a separate module
#[cfg(feature = "ssr")]
mod db {
    use sqlx::*;
    // ...
}
```

## Server Functions

### Server function not found (404)

**Problem**: Server function not registered.

Causes:
1. Different path on client vs server
2. Function not compiled for server
3. Missing server integration setup

**Solution**: Verify registration.

```rust
// Check the path matches
#[server(endpoint = "/api/custom")]  // Explicit path
async fn my_fn() -> Result<(), ServerFnError> { }

// Ensure feature flags are correct
// Server build: features = ["ssr"]
// Client build: features = ["hydrate"]
```

### Server function returns wrong error

**Problem**: Error type doesn't serialize correctly.

```rust
// BAD - custom error without proper handling
#[server]
async fn risky() -> Result<Data, ServerFnError> {
    let data = external_crate::fetch()
        .await?;  // May not convert properly
    Ok(data)
}
```

**Solution**: Explicitly convert errors.

```rust
// GOOD - explicit conversion
#[server]
async fn risky() -> Result<Data, ServerFnError> {
    let data = external_crate::fetch()
        .await
        .map_err(|e| ServerFnError::ServerError(e.to_string()))?;
    Ok(data)
}
```

### Action/Resource not updating

**Problem**: Missing reactive wrapper.

```rust
// BAD - not reactive
let action = ServerAction::<MyFn>::new();
let is_pending = action.pending().get();  // Snapshot!

view! {
    <button disabled=is_pending>  // Never updates
        "Submit"
    </button>
}
```

**Solution**: Wrap in closure.

```rust
// GOOD - reactive
let action = ServerAction::<MyFn>::new();

view! {
    <button disabled=move || action.pending().get()>
        "Submit"
    </button>
}
```

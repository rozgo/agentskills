# Reactive Stores Reference

## Table of Contents
- [Overview](#overview)
- [Defining Stores](#defining-stores)
- [Accessing Fields](#accessing-fields)
- [Updating Stores](#updating-stores)
- [Keyed Collections](#keyed-collections)
- [When to Use Stores](#when-to-use-stores)

## Overview

Stores provide fine-grained reactivity for deeply nested state. Unlike signals (which notify on any change), stores track changes at the field level.

Benefits:
- Plain Rust structs (no wrapper types for fields)
- Efficient updates (only changed fields notify)
- Arbitrarily deep nesting
- Natural Rust ergonomics

## Defining Stores

### Basic Store

```rust
use leptos::prelude::*;
use reactive_stores::Store;

#[derive(Clone, Debug, Store)]
pub struct AppState {
    pub user: User,
    pub settings: Settings,
    pub items: Vec<Item>,
}

#[derive(Clone, Debug, Store)]
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}

#[derive(Clone, Debug, Store)]
pub struct Settings {
    pub theme: String,
    pub notifications: bool,
}

#[derive(Clone, Debug, Store)]
pub struct Item {
    pub id: u64,
    pub title: String,
    pub completed: bool,
}
```

### Creating a Store Instance

```rust
#[component]
pub fn App() -> impl IntoView {
    let state = Store::new(AppState {
        user: User {
            id: 1,
            name: "Alice".into(),
            email: "alice@example.com".into(),
        },
        settings: Settings {
            theme: "light".into(),
            notifications: true,
        },
        items: vec![],
    });

    // Provide to descendants
    provide_context(state);

    view! { /* ... */ }
}
```

## Accessing Fields

### Reading Fields

Each field becomes a reactive accessor:

```rust
#[component]
fn UserDisplay() -> impl IntoView {
    let state = expect_context::<Store<AppState>>();

    // Access nested fields - each is independently reactive
    let name = move || state.user().name().get();
    let email = move || state.user().email().get();
    let theme = move || state.settings().theme().get();

    view! {
        <div>
            <p>"Name: " {name}</p>
            <p>"Email: " {email}</p>
            <p>"Theme: " {theme}</p>
        </div>
    }
}
```

### Field Reactivity

Only components reading changed fields re-render:

```rust
#[component]
fn NameOnly() -> impl IntoView {
    let state = expect_context::<Store<AppState>>();

    // Only re-renders when name changes
    // NOT when email or settings change
    view! {
        <p>{move || state.user().name().get()}</p>
    }
}

#[component]
fn SettingsOnly() -> impl IntoView {
    let state = expect_context::<Store<AppState>>();

    // Only re-renders when settings.theme changes
    view! {
        <p>{move || state.settings().theme().get()}</p>
    }
}
```

## Updating Stores

### Direct Field Updates

```rust
#[component]
fn UpdateExample() -> impl IntoView {
    let state = expect_context::<Store<AppState>>();

    let update_name = move |_| {
        // Update specific field
        state.user().name().set("Bob".into());
    };

    let toggle_notifications = move |_| {
        // Update with closure
        state.settings().notifications().update(|n| *n = !*n);
    };

    view! {
        <button on:click=update_name>"Change Name"</button>
        <button on:click=toggle_notifications>"Toggle Notifications"</button>
    }
}
```

### Batch Updates

Update multiple fields efficiently:

```rust
let update_user = move |_| {
    // Both updates batched, single notification
    batch(|| {
        state.user().name().set("Charlie".into());
        state.user().email().set("charlie@example.com".into());
    });
};
```

### Patching

Replace parts of state with new values:

```rust
use reactive_stores::Patch;

// Patch updates only changed fields
state.user().patch(User {
    id: 1,          // Same - no notification
    name: "New".into(),  // Changed - notifies
    email: "same@example.com".into(),  // Same - no notification
});
```

## Keyed Collections

### Defining Keyed Collections

For efficient list rendering, specify a key function:

```rust
#[derive(Clone, Debug, Store)]
pub struct TodoList {
    #[store(key: u64 = |todo| todo.id)]
    pub todos: Vec<Todo>,
}

#[derive(Clone, Debug, Store)]
pub struct Todo {
    pub id: u64,
    pub title: String,
    pub completed: bool,
}
```

### Iterating Keyed Collections

```rust
#[component]
fn TodoList() -> impl IntoView {
    let state = expect_context::<Store<TodoList>>();

    view! {
        <ul>
            <For
                each=move || state.todos()
                key=|todo| todo.id().get()
                let:todo
            >
                <TodoItem todo />
            </For>
        </ul>
    }
}

#[component]
fn TodoItem(#[prop(into)] todo: Field<Todo>) -> impl IntoView {
    view! {
        <li class:completed=move || todo.completed().get()>
            <span>{move || todo.title().get()}</span>
            <button on:click=move |_| todo.completed().update(|c| *c = !*c)>
                "Toggle"
            </button>
        </li>
    }
}
```

### Modifying Collections

```rust
let state = expect_context::<Store<TodoList>>();

// Add item
let add_todo = move |_| {
    state.todos().write().push(Todo {
        id: next_id(),
        title: "New Todo".into(),
        completed: false,
    });
};

// Remove item
let remove_todo = move |id: u64| {
    state.todos().write().retain(|t| t.id != id);
};

// Update item by key
let toggle_todo = move |id: u64| {
    if let Some(todo) = state.todos().iter().find(|t| t.id().get() == id) {
        todo.completed().update(|c| *c = !*c);
    }
};
```

## When to Use Stores

### Use Stores When:

1. **Deep nesting** - State has multiple levels
   ```rust
   app.user.profile.settings.theme  // Store is better
   ```

2. **Large objects** - Many fields, few change at once
   ```rust
   #[derive(Store)]
   struct Form {
       field1: String,  // Only field1 updates notify field1 readers
       field2: String,
       // ... 20 more fields
   }
   ```

3. **Collections with identity** - Lists where items have IDs
   ```rust
   #[store(key: u64 = |item| item.id)]
   items: Vec<Item>
   ```

### Use Signals When:

1. **Simple values** - Primitives or small structs
   ```rust
   let count = RwSignal::new(0);
   let name = RwSignal::new(String::new());
   ```

2. **Atomic updates** - Entire value changes together
   ```rust
   let position = RwSignal::new((x, y));  // Both change together
   ```

3. **Independent state** - Unrelated values
   ```rust
   let modal_open = RwSignal::new(false);
   let selected_id = RwSignal::new(None);
   ```

### Combining Stores and Signals

```rust
#[derive(Clone, Debug, Store)]
struct AppState {
    // Store for nested data
    pub user: User,
    pub todos: Vec<Todo>,
}

#[component]
fn App() -> impl IntoView {
    let state = Store::new(initial_state());

    // Separate signals for UI state
    let modal_open = RwSignal::new(false);
    let filter = RwSignal::new(Filter::All);

    provide_context(state);
    provide_context(modal_open);
    provide_context(filter);

    view! { /* ... */ }
}
```

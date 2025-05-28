/**
 * Component Registry for dynamic component loading
 * This allows us to register components and retrieve them by name
 */

class ComponentRegistry {
  constructor() {
    this.components = new Map();
  }

  /**
   * Register a component with a name
   * @param {string} name - The name to register the component under
   * @param {React.Component} component - The React component to register
   */
  register(name, component) {
    if (!name || !component) {
      throw new Error('Both name and component are required for registration');
    }
    this.components.set(name, component);
    console.log(`[ComponentRegistry] Registered component: ${name}`);
  }

  /**
   * Get a component by name
   * @param {string} name - The name of the component to retrieve
   * @returns {React.Component|null} The component or null if not found
   */
  get(name) {
    const component = this.components.get(name);
    if (!component) {
      console.warn(`[ComponentRegistry] Component not found: ${name}`);
    }
    return component || null;
  }

  /**
   * Check if a component is registered
   * @param {string} name - The name to check
   * @returns {boolean} True if the component is registered
   */
  has(name) {
    return this.components.has(name);
  }

  /**
   * Get all registered component names
   * @returns {string[]} Array of registered component names
   */
  getRegisteredNames() {
    return Array.from(this.components.keys());
  }

  /**
   * Unregister a component
   * @param {string} name - The name of the component to unregister
   */
  unregister(name) {
    if (this.components.delete(name)) {
      console.log(`[ComponentRegistry] Unregistered component: ${name}`);
    }
  }
}

// Create and export a singleton instance
export const componentRegistry = new ComponentRegistry(); 
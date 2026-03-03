import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import LoginPage from '../LoginPage';

describe('LoginPage', () => {
  let onLogin;

  beforeEach(() => {
    onLogin = vi.fn();
    global.fetch = vi.fn();
  });

  it('renders login form with username and password fields', () => {
    render(<LoginPage onLogin={onLogin} />);
    expect(screen.getByLabelText(/username/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeTruthy();
  });

  it('switches between login and register modes', () => {
    render(<LoginPage onLogin={onLogin} />);
    const registerTab = screen.getByRole('button', { name: /register/i });
    fireEvent.click(registerTab);
    expect(screen.getByRole('button', { name: /create account/i })).toBeTruthy();
  });

  it('calls onLogin with token on successful login', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: 'test-jwt', username: 'user1' }),
    });

    render(<LoginPage onLogin={onLogin} />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'user1' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'pass' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(onLogin).toHaveBeenCalledWith('test-jwt'));
  });

  it('shows error message on failed login', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' }),
    });

    render(<LoginPage onLogin={onLogin} />);
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'user1' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeTruthy();
    });
    expect(onLogin).not.toHaveBeenCalled();
  });
});

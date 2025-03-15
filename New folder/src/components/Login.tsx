import { Link } from 'react-router-dom';
import { useState } from 'react';

interface LoginPageProps {
  onLogin: (email: string, password: string) => Promise<void>;
  error: string | null;
  loading: boolean;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, error, loading }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onLogin(email, password);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <form 
        onSubmit={handleSubmit}
        className="bg-card p-8 rounded-lg shadow-md w-full max-w-md border border-border"
      >
        <h2 className="text-2xl font-bold mb-6 text-foreground">Login</h2>
        {error && <div className="mb-4 text-red-500">{error}</div>}

        <div className="mb-4">
          <label className="block text-foreground mb-2">E-Mail</label>
          <input 
            type="email" 
            value={email}
            placeholder="Enter your email"
            title="Email"
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-2 border border-border rounded focus:ring-2 focus:ring-primary"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-foreground mb-2">Password</label>
          <input 
            type="password"
            placeholder="Enter your password"
            title="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 border border-border rounded focus:ring-2 focus:ring-primary"
            required
          />
        </div>

        <button 
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-primary-foreground py-2 rounded hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? 'Signing In...' : 'Sign In'}
        </button>

        <div className="mt-4 text-center">
          <Link 
            to="/forgot-password" 
            className="text-primary hover:text-primary/80"
          >
            Forgot Password ?
          </Link>
        </div>
        
        <div className="mt-4 text-center">
          <span className="text-muted-foreground">Don't Have An Account ? </span>
          <Link 
            to="/signup" 
            className="text-primary hover:text-primary/80"
          >
            Sign Up
          </Link>
        </div>
      </form>
    </div>
  );
};

export default LoginPage;

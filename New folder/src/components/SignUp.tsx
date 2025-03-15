import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

const SignupPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      navigate('/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <form 
        onSubmit={handleSubmit}
        className="bg-card p-8 rounded-lg shadow-md w-full max-w-md border border-border"
      >
        <h2 className="text-2xl font-bold mb-6 text-foreground">Create Account</h2>
        {error && <div className="mb-4 text-red-500">{error}</div>}

        <div className="mb-4">
          <label className="block text-foreground mb-2">Username</label>
          <input 
            type="text" 
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            title="Username"
            className="w-full p-2 border border-border rounded focus:ring-2 focus:ring-primary"
            required
            placeholder="Enter your username"
          />
        </div>

        <div className="mb-4">
          <label className="block text-foreground mb-2">E-Mail</label>
          <input 
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            title="Email"
            placeholder="Enter your email"
            className="w-full p-2 border border-border rounded focus:ring-2 focus:ring-primary"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-foreground mb-2">Password</label>
          <input 
            type="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            title="Password"
            placeholder="Enter your password"
            className="w-full p-2 border border-border rounded focus:ring-2 focus:ring-primary"
            required
          />
        </div>

        <button 
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-primary-foreground py-2 rounded hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? 'Creating Account...' : 'Create Account'}
        </button>

        <div className="mt-4 text-center">
          <span className="text-muted-foreground">Already Have An Account ? </span>
          <Link 
            to="/login" 
            className="text-primary hover:text-primary/80"
          >
            Login
          </Link>
        </div>
      </form>
    </div>
  );
};

export default SignupPage;

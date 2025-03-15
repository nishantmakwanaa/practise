import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('http://localhost:5000/api/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, new_password: newPassword }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Password reset failed');
      }

      setSuccess('Password updated successfully!');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Password reset failed');
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
        <h2 className="text-2xl font-bold mb-6 text-foreground">Reset Password</h2>
        {error && <div className="mb-4 text-red-500">{error}</div>}
        {success && <div className="mb-4 text-green-500">{success}</div>}

        <div className="mb-4">
          <label className="block text-foreground mb-2">E-Mail</label>
          <input 
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="w-full p-2 border border-border rounded focus:ring-2 focus:ring-primary"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-foreground mb-2">New Password</label>
          <input 
            type="password" 
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Enter your new password"
            className="w-full p-2 border border-border rounded focus:ring-2 focus:ring-primary"
            required
          />
        </div>

        <button 
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-primary-foreground py-2 rounded hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? 'Resetting...' : 'Reset Password'}
        </button>

        <div className="mt-4 text-center">
          <Link 
            to="/login" 
            className="text-primary hover:text-primary/80"
          >
            Back To Login
          </Link>
        </div>
      </form>
    </div>
  );
};

export default ForgotPasswordPage;

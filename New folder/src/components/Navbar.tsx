interface NavbarProps {
  onLogout: () => void;
}

const Navbar = ({ onLogout }: NavbarProps) => {
  return (
    <nav className="bg-blue-600 text-white p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <div className="font-bold text-xl">Milople - AI Code Editor</div>
        <div className="flex space-x-4">
          <span className="px-2 py-1 bg-blue-700 rounded text-sm">Build By Team Phoenix</span>
          <button
            onClick={onLogout}
            className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-sm transition-colors"
          >
            Log Out
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 
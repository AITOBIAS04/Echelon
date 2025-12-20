import { ReactNode } from 'react';

interface TerminalProps {
  children: ReactNode;
}

const Terminal = ({ children }: TerminalProps) => {
  return (
    <main className="flex-1 overflow-auto">
      <div className="h-full p-6">
        {children}
      </div>
    </main>
  );
};

export default Terminal;



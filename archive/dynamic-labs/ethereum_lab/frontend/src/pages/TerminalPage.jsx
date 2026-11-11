/**
 * TerminalPage - Standalone Lab Terminal for popup/new tab.
 * Open via /terminal so the main app stays visible while deploying.
 * Pass ?rpc=http://... to connect to instructor's node.
 */

import { useSearchParams } from 'react-router-dom';
import TerminalPopup from '../components/TerminalPopup';

export default function TerminalPage() {
  const [searchParams] = useSearchParams();
  const rpcUrl = searchParams.get('rpc') || '';
  const terminalRpcUrl = searchParams.get('trpc') || '';

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0f172a' }}>
      <TerminalPopup
        open={true}
        onClose={() => window.close()}
        rpcUrl={rpcUrl}
        terminalRpcUrl={terminalRpcUrl}
      />
    </div>
  );
}

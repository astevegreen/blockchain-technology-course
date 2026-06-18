let nodeContext = null;

function closeHelpModal() {
  const backdrop = document.getElementById('helpBackdrop');
  if (!backdrop) return;
  backdrop.classList.remove('open');
  backdrop.setAttribute('aria-hidden', 'true');
}

function openHelpModal() {
  const backdrop = document.getElementById('helpBackdrop');
  if (!backdrop) return;
  backdrop.classList.add('open');
  backdrop.setAttribute('aria-hidden', 'false');
}

function consoleBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withConsoleBase(path) {
  return `${consoleBasePath()}${path}`;
}

function currentNodeKey() {
  const path = window.location.pathname;
  if (path.includes('/peer/org1/console/')) return 'org1';
  if (path.includes('/peer/org2/console/')) return 'org2';
  if (path.includes('/peer/org3/console/')) return 'org3';
  if (path.includes('/peer/org4/console/')) return 'org4';
  if (path.includes('/peer/org5/console/')) return 'org5';
  return 'orderer';
}

function currentNodeLabel() {
  const mapping = {
    org1: 'Cascadia State University (peer0.cascadiastate.example.com)',
    org2: 'Chesapeake Canoe University (peer0.chesapeakecanoe.example.com)',
    org3: 'South Hudson Institute of Technology (peer0.southhudson.example.com)',
    org4: 'Maple Leaf Academy (peer0.mapleleaf.example.com)',
    org5: 'Meridian Industries (peer0.meridian.example.com) — read-only verifier',
    orderer: 'orderer.example.com',
  };
  return mapping[currentNodeKey()];
}

function currentTerminalPath() {
  // Instructor terminal paths are always absolute — they must not
  // inherit a student claim prefix from HLFBase.
  return `/labs/hlf/instructor/term/${currentNodeKey()}/`;
}

function currentOrgDisplay() {
  const mapping = {
    org1: 'Cascadia State University (Org1MSP)',
    org2: 'Chesapeake Canoe University (Org2MSP)',
    org3: 'South Hudson Institute of Technology (Org3MSP)',
    org4: 'Maple Leaf Academy (Org4MSP)',
    org5: 'Meridian Industries (Org5MSP) — not in endorsement policy',
    orderer: 'Ordering Service (OrdererMSP)',
  };
  return mapping[currentNodeKey()];
}

function exerciseCommands() {
  const key = currentNodeKey();
  if (key === 'orderer') {
    return [
      'hlf-help                                  # show available commands',
      'channel-info                              # show current channel height and block info',
      'ls /var/hyperledger/production/orderer    # see the orderer ledger files',
    ];
  }
  if (key === 'org5') {
    return [
      'hlf-help                                                           # show available commands',
      'query diploma-001                                                  # read a diploma (works: query path is open to channel members)',
      'list-assets                                                        # list all diplomas on the shared ledger',
      'invoke create diploma-forged credential 4 "Fake" 2024 "X" "BSc"    # fails — Org5 is not in the endorsement policy',
    ];
  }
  return [
    'hlf-help                                                                                  # list lab commands',
    'query diploma-001                                                                         # read an asset from the ledger',
    'invoke create diploma-002 credential 4 "Susan B. Anthony" 2024 "History" "Master of Arts"  # issue a new diploma',
    'list-assets                                                                               # list all assets in world state',
  ];
}

function renderContext() {
  const workingDir = currentNodeKey() === 'orderer'
    ? '/var/hyperledger/orderer'
    : '/etc/hyperledger/fabric';
  document.getElementById('contextSummary').innerHTML =
    `Working directory: <code>${workingDir}</code> &middot; Org: <code>${currentOrgDisplay()}</code>`;
  const list = document.getElementById('quickCommands');
  list.innerHTML = '';
  exerciseCommands().forEach((command) => {
    const item = document.createElement('li');
    const code = document.createElement('code');
    code.textContent = command;
    item.appendChild(code);
    list.appendChild(item);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const helpBtn = document.getElementById('helpBtn');
  const helpClose = document.getElementById('helpClose');
  const helpBackdrop = document.getElementById('helpBackdrop');
  const terminalFrame = document.getElementById('terminalFrame');

  if (helpBtn) helpBtn.addEventListener('click', openHelpModal);
  if (helpClose) helpClose.addEventListener('click', closeHelpModal);
  if (helpBackdrop) {
    helpBackdrop.addEventListener('click', (event) => {
      if (event.target === helpBackdrop) closeHelpModal();
    });
  }
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeHelpModal();
  });

  document.getElementById('title').textContent = `HLF Node Console: ${currentNodeLabel()}`;
  document.getElementById('subtitle').textContent = `Real zellij-backed shell access for ${currentNodeLabel()}`;
  let resizeTimer = null;
  function notifyTerminalResize() {
    const child = terminalFrame && terminalFrame.contentWindow;
    if (!child) return;
    try {
      const EventCtor = child.Event || Event;
      child.dispatchEvent(new EventCtor('resize'));
    } catch (_) {}
  }

  function installTerminalResizeBridge() {
    const child = terminalFrame && terminalFrame.contentWindow;
    if (!child) return;
    try {
      if (child.__labTerminalResizeBridgeInstalled) return;
      const doc = child.document;
      const target = doc && (doc.documentElement || doc.body);
      if (!target || !child.ResizeObserver) return;
      child.__labTerminalResizeBridgeInstalled = true;
      child.__labTerminalResizeBridge = new child.ResizeObserver(function () {
        try {
          child.dispatchEvent(new child.Event('resize'));
        } catch (_) {}
      });
      child.__labTerminalResizeBridge.observe(target);
    } catch (_) {}
  }

  function forceTerminalResize() {
    installTerminalResizeBridge();
    notifyTerminalResize();
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(function () {
        installTerminalResizeBridge();
        notifyTerminalResize();
      });
    }
    setTimeout(notifyTerminalResize, 120);
    setTimeout(notifyTerminalResize, 300);
  }

  function scheduleTerminalResize(delay) {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      resizeTimer = null;
      forceTerminalResize();
    }, typeof delay === 'number' ? delay : 80);
  }
  if (terminalFrame) {
    terminalFrame.addEventListener('load', scheduleTerminalResize);
    terminalFrame.src = currentTerminalPath();
    window.addEventListener('resize', scheduleTerminalResize);
    if (window.ResizeObserver) {
      const observer = new ResizeObserver(scheduleTerminalResize);
      observer.observe(terminalFrame);
    }
  }
  renderContext();
});

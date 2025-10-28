# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Multi-chain wallet that automatically selects the right signing method based on network."""

from x402_a2a.types import PaymentPayload, x402PaymentRequiredResponse
from .wallet import Wallet, MockLocalWallet
from .solana_wallet import SolanaWallet


class MultiChainWallet(Wallet):
    """
    A wallet that automatically detects the payment network and uses the appropriate signer.
    
    Supports both EVM (Ethereum, Base, etc.) and SVM (Solana) networks.
    """

    def __init__(self, evm_wallet: Wallet = None, solana_wallet: SolanaWallet = None):
        """
        Initialize with separate wallets for each chain.
        
        Args:
            evm_wallet: Wallet for EVM chains (defaults to MockLocalWallet)
            solana_wallet: Wallet for Solana (defaults to generated SolanaWallet)
        """
        self.evm_wallet = evm_wallet or MockLocalWallet()
        self.solana_wallet = solana_wallet or SolanaWallet.generate()

    def sign_payment(self, requirements: x402PaymentRequiredResponse) -> PaymentPayload:
        """
        Signs payment requirements using the appropriate wallet based on network.
        
        Args:
            requirements: Payment requirements from the merchant
            
        Returns:
            PaymentPayload signed by the appropriate wallet
            
        Raises:
            ValueError: If network is not supported
        """
        # Get the first payment requirement to check the network
        if not requirements.accepts or len(requirements.accepts) == 0:
            raise ValueError("No payment requirements provided")
        
        first_requirement = requirements.accepts[0]
        network = first_requirement.network
        
        # Detect network type and use appropriate wallet
        if network in ["solana", "solana-devnet"]:
            print(f"🟣 Using Solana wallet for network: {network}")
            return self.solana_wallet.sign_payment(requirements)
        elif network in ["base", "base-sepolia", "ethereum", "avalanche", "avalanche-fuji"]:
            print(f"🔵 Using EVM wallet for network: {network}")
            return self.evm_wallet.sign_payment(requirements)
        else:
            raise ValueError(
                f"Unsupported network: {network}. "
                f"Supported networks: solana, solana-devnet, base, base-sepolia, ethereum"
            )

    @classmethod
    def create_demo_wallet(cls) -> "MultiChainWallet":
        """
        Create a demo wallet with mock keys for testing.
        
        Returns:
            MultiChainWallet with generated test wallets
        """
        return cls(
            evm_wallet=MockLocalWallet(),
            solana_wallet=SolanaWallet.generate(),
        )




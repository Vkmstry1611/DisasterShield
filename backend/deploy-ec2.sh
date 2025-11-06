#!/bin/bash

# DisasterShield EC2 Deployment Script
echo "🚀 Deploying DisasterShield on EC2..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "📦 Installing Docker..."
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Git
sudo apt install -y git

# Clone repository (replace with your GitHub URL)
echo "📥 Cloning repository..."
git clone https://github.com/YOUR_USERNAME/DisasterShield.git
cd DisasterShield/backend

# Create environment file
echo "⚙️ Setting up environment..."
cat > .env << EOF
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=DisasterShield:v1.0:by-student
JWT_SECRET_KEY=DisasterShield-EC2-Secret-Key-2024
DATABASE_URL=postgresql://postgres:password@localhost:5432/disastershield_db
EOF

# Build and run with Docker Compose
echo "🐳 Starting Docker containers..."
sudo docker-compose up -d

# Show status
echo "✅ Deployment complete!"
echo "🌐 Your app should be running on: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "🔍 Check status: sudo docker-compose ps"
echo "📋 View logs: sudo docker-compose logs -f"

# Setup firewall
echo "🔒 Configuring firewall..."
sudo ufw allow 22    # SSH
sudo ufw allow 8000  # Your app
sudo ufw --force enable

echo "🎉 DisasterShield is now running on EC2!"
echo "📱 Update your React Native app to use: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
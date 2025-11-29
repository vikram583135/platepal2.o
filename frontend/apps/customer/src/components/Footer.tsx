import { Link } from 'react-router-dom'
import { Facebook, Twitter, Instagram, Linkedin } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-red-50/50 border-t border-red-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <h3 className="text-2xl font-bold text-zomato-red">PlatePal</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Experience the best food delivery service. Fresh, fast, and delicious meals delivered right to your doorstep.
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/about" className="hover:text-zomato-red transition-colors">About Us</Link></li>
              <li><Link to="/careers" className="hover:text-zomato-red transition-colors">Careers</Link></li>
              <li><Link to="/blog" className="hover:text-zomato-red transition-colors">Blog</Link></li>
              <li><Link to="/contact" className="hover:text-zomato-red transition-colors">Contact</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Support</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/help" className="hover:text-zomato-red transition-colors">Help Center</Link></li>
              <li><Link to="/faq" className="hover:text-zomato-red transition-colors">FAQs</Link></li>
              <li><Link to="/terms" className="hover:text-zomato-red transition-colors">Terms of Service</Link></li>
              <li><Link to="/privacy" className="hover:text-zomato-red transition-colors">Privacy Policy</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Connect with Us</h4>
            <div className="flex gap-4">
              <a href="#" className="text-muted-foreground hover:text-zomato-red transition-colors">
                <Facebook className="h-5 w-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-zomato-red transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-zomato-red transition-colors">
                <Instagram className="h-5 w-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-zomato-red transition-colors">
                <Linkedin className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t text-center text-sm text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} PlatePal. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}


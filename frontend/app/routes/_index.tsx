import { Link } from 'react-router';
import { motion } from 'motion/react';
import { useRef } from 'react';
import {
  Github,
  Sparkles,
  FileText,
  ArrowRight,
  Users,
  Settings,
  Target,
  History,
} from 'lucide-react';

export default function HomePage() {
  const advancedFeaturesRef = useRef<HTMLElement>(null);

  // Optimized hover variants (removed fade-in)
  const hoverScale = { scale: 1.02 };
  const tapScale = { scale: 0.98 };
  const cardHover = { y: -2, scale: 1.02 };

  const quickTransition = { duration: 0.15, ease: 'easeOut' as const };

  return (
    <div className='space-y-16'>
      {/* Hero Section */}
      <section className='text-center space-y-8'>
        <div className='space-y-4'>
          <h1 className='text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight'>
            AI-Powered LinkedIn
            <motion.span
              className='block text-blue-600'
              whileHover={hoverScale}
              transition={quickTransition}
              style={{ willChange: 'transform' }}
            >
              Recommendation Writer
            </motion.span>
          </h1>
          <p className='text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed'>
            Generate personalized LinkedIn recommendations for GitHub
            contributors using AI. Analyze commits, PRs, and add your personal
            experience to create compelling recommendations.
          </p>
        </div>

        <div className='flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-center max-w-md sm:max-w-none mx-auto'>
          <motion.div
            whileHover={hoverScale}
            whileTap={tapScale}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <Link
              to='/generate'
              className='inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-blue-600 text-white shadow hover:bg-blue-700 active:bg-blue-800 h-10 px-8 space-x-2'
            >
              <Sparkles className='w-5 h-5' />
              <span>Generate Recommendation</span>
              <ArrowRight className='w-4 h-4' />
            </Link>
          </motion.div>
          <motion.div
            whileHover={hoverScale}
            whileTap={tapScale}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <Link
              to='/about'
              className='inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-gray-300 bg-white text-gray-700 shadow-sm hover:bg-gray-50 active:bg-gray-100 h-10 px-8 space-x-2'
            >
              <FileText className='w-5 h-5' />
              <span>Learn More</span>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section className='space-y-12'>
        <div className='text-center'>
          <h2 className='text-3xl font-bold text-gray-900 mb-4'>
            How It Works
          </h2>
          <p className='text-lg text-gray-600 max-w-2xl mx-auto'>
            Generate professional LinkedIn recommendations in three simple steps
          </p>
        </div>

        <div className='grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8'>
          <motion.div
            className='text-center space-y-4'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto'
              whileHover={{ rotate: 90 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <Github className='w-8 h-8 text-blue-600' />
            </motion.div>
            <h3 className='text-xl font-semibold text-gray-900'>
              1. Find Contributors
            </h3>
            <p className='text-gray-600'>
              Enter a repository name to discover all contributors with their
              GitHub profiles and contribution history
            </p>
          </motion.div>

          <motion.div
            className='text-center space-y-4'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto'
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <Users className='w-8 h-8 text-green-600' />
            </motion.div>
            <h3 className='text-xl font-semibold text-gray-900'>
              2. Add Your Experience
            </h3>
            <p className='text-gray-600'>
              Select a contributor and describe your working relationship,
              projects, and their key skills
            </p>
          </motion.div>

          <motion.div
            className='text-center space-y-4'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto'
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <Sparkles className='w-8 h-8 text-purple-600' />
            </motion.div>
            <h3 className='text-xl font-semibold text-gray-900'>
              3. AI-Generated Recommendation
            </h3>
            <p className='text-gray-600'>
              Get a personalized LinkedIn recommendation combining GitHub data
              with your personal insights
            </p>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className='bg-white rounded-lg shadow-sm p-8 space-y-8'>
        <div className='text-center'>
          <h2 className='text-3xl font-bold text-gray-900 mb-4'>Features</h2>
          <p className='text-lg text-gray-600'>
            Everything you need to create compelling LinkedIn recommendations
          </p>
        </div>

        <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6'>
          <motion.div
            className='space-y-3'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center'
              whileHover={{ rotate: 90 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <Sparkles className='w-6 h-6 text-blue-600' />
            </motion.div>
            <h3 className='font-semibold text-gray-900'>
              AI-Powered Generation
            </h3>
            <p className='text-sm text-gray-600'>
              Advanced AI analyzes GitHub activity and your input to create
              compelling recommendations
            </p>
          </motion.div>

          <motion.div
            className='space-y-3'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center'
              whileHover={{ rotate: 90 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <Github className='w-6 h-6 text-green-600' />
            </motion.div>
            <h3 className='font-semibold text-gray-900'>GitHub Integration</h3>
            <p className='text-sm text-gray-600'>
              Automatically fetches commits, PRs, and code contributions to
              understand technical skills
            </p>
          </motion.div>

          <motion.div
            className='space-y-3'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center'
              whileHover={{ rotate: 90 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <Users className='w-6 h-6 text-purple-600' />
            </motion.div>
            <h3 className='font-semibold text-gray-900'>Personal Context</h3>
            <p className='text-sm text-gray-600'>
              Combine technical data with your personal experience working
              together
            </p>
          </motion.div>

          <motion.div
            className='space-y-3'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center'
              whileHover={{ rotate: 90 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <FileText className='w-6 h-6 text-orange-600' />
            </motion.div>
            <h3 className='font-semibold text-gray-900'>Multiple Formats</h3>
            <p className='text-sm text-gray-600'>
              Choose from professional, technical, leadership styles with
              different tones and lengths
            </p>
          </motion.div>

          <motion.div
            className='space-y-3'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center'
              whileHover={{ rotate: 90 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <ArrowRight className='w-6 h-6 text-red-600' />
            </motion.div>
            <h3 className='font-semibold text-gray-900'>One-Click Copy</h3>
            <p className='text-sm text-gray-600'>
              Generated recommendations are ready to copy and paste directly
              into LinkedIn
            </p>
          </motion.div>

          <motion.div
            className='space-y-3'
            whileHover={cardHover}
            transition={quickTransition}
            style={{ willChange: 'transform' }}
          >
            <motion.div
              className='w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center'
              whileHover={{ rotate: 90 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              style={{ willChange: 'transform' }}
            >
              <FileText className='w-6 h-6 text-indigo-600' />
            </motion.div>
            <h3 className='font-semibold text-gray-900'>
              History & Management
            </h3>
            <p className='text-sm text-gray-600'>
              Keep track of all generated recommendations with full history and
              management
            </p>
          </motion.div>
        </div>
      </section>

      {/* Advanced Features */}
      <section
        id='advanced-features'
        ref={advancedFeaturesRef}
        className='bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-8 space-y-8'
      >
        <div className='text-center'>
          <h2 className='text-3xl font-bold text-gray-900 mb-4'>
            Advanced Features
          </h2>
          <p className='text-lg text-gray-600'>
            Unlock powerful new capabilities for professional recommendation
            writing
          </p>
        </div>

        <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6'>
          <div className='space-y-3'>
            <div className='w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center'>
              <Settings className='w-6 h-6 text-purple-600' />
            </div>
            <h3 className='font-semibold text-gray-900'>Keyword Refinement</h3>
            <p className='text-sm text-gray-600'>
              Fine-tune recommendations by specifying keywords to include or
              exclude for precise customization
            </p>
          </div>

          <div className='text-center'>
            <div className='w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center'>
              <FileText className='w-6 h-6 text-green-600' />
            </div>
            <h3 className='font-semibold text-gray-900'>
              Documentation Insights
            </h3>
            <p className='text-sm text-gray-600'>
              Extract valuable insights from your GitHub repositories and
              present them in professional recommendations
            </p>
          </div>

          <div className='text-center'>
            <div className='w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center'>
              <Target className='w-6 h-6 text-orange-600' />
            </div>
            <h3 className='font-semibold text-gray-900'>
              Smart Recommendations
            </h3>
            <p className='text-sm text-gray-600'>
              Generate intelligent, personalized LinkedIn recommendations
              tailored to your unique profile and goals
            </p>
          </div>

          <div className='space-y-3'>
            <div className='w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center'>
              <History className='w-6 h-6 text-blue-600' />
            </div>
            <h3 className='font-semibold text-gray-900'>Version History</h3>
            <p className='text-sm text-gray-600'>
              Track changes, compare versions, and revert recommendations with
              full history management
            </p>
          </div>

          <div className='space-y-3'>
            <div className='w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center'>
              <Users className='w-6 h-6 text-red-600' />
            </div>
            <h3 className='font-semibold text-gray-900'>
              Repository Contributors
            </h3>
            <p className='text-sm text-gray-600'>
              Find and analyze contributors from any GitHub repository for
              personalized recommendations
            </p>
          </div>

          <div className='space-y-3'>
            <div className='w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center'>
              <Sparkles className='w-6 h-6 text-indigo-600' />
            </div>
            <h3 className='font-semibold text-gray-900'>
              Enhanced AI Analysis
            </h3>
            <p className='text-sm text-gray-600'>
              Advanced AI with conventional commit parsing, dependency analysis,
              and improved confidence scoring
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <motion.section
        className='bg-blue-600 rounded-lg text-white p-8 text-center space-y-6'
        whileHover={hoverScale}
        transition={quickTransition}
        style={{ willChange: 'transform' }}
      >
        <div>
          <h2 className='text-3xl font-bold'>
            Ready to Write Amazing Recommendations?
          </h2>
          <p className='text-xl text-blue-100 max-w-2xl mx-auto'>
            Generate personalized LinkedIn recommendations in minutes, not hours
          </p>
        </div>
        <motion.div
          whileHover={hoverScale}
          whileTap={tapScale}
          transition={quickTransition}
          style={{ willChange: 'transform' }}
        >
          <Link
            to='/generate'
            className='inline-flex items-center space-x-2 bg-white text-blue-600 px-6 py-3 rounded-md font-medium hover:bg-gray-50 transition-colors'
          >
            <Sparkles className='w-5 h-5' />
            <span>Generate Recommendation</span>
            <ArrowRight className='w-4 h-4' />
          </Link>
        </motion.div>
      </motion.section>
    </div>
  );
}

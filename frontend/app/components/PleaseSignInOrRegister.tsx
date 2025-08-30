import { Button } from '@/components/ui/button';
import { Link } from 'react-router';
import { motion } from 'motion/react';
import { Sparkles, FileText, History, Zap, Users } from 'lucide-react';

export const PleaseSignInOrRegister = () => {
  const containerVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.6,
        staggerChildren: 0.15,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
    },
  };

  const sparkleVariants = {
    animate: {
      scale: [1, 1.2, 1],
      opacity: [0.7, 1, 0.7],
    },
  };

  const transitionSettings = {
    duration: 0.5,
    ease: 'easeOut' as const,
  };

  const sparkleTransition = {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut' as const,
  };

  return (
    <motion.div
      className='flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-4'
      variants={containerVariants}
      initial='hidden'
      animate='visible'
      transition={transitionSettings}
    >
      <motion.div
        className='bg-white p-8 rounded-xl shadow-xl text-center max-w-2xl w-full border border-gray-100'
        variants={itemVariants}
        transition={transitionSettings}
      >
        <motion.div className='relative mb-6' variants={itemVariants}>
          <motion.div
            variants={sparkleVariants}
            animate='animate'
            transition={sparkleTransition}
            style={{ animationDelay: '0s' }}
          >
            <Sparkles className='w-6 h-6 text-yellow-400 absolute -top-2 -right-8' />
          </motion.div>
          <motion.div
            variants={sparkleVariants}
            animate='animate'
            transition={sparkleTransition}
            style={{ animationDelay: '1s' }}
          >
            <Sparkles className='w-4 h-4 text-pink-400 absolute -bottom-2 -left-8' />
          </motion.div>
        </motion.div>

        <motion.h1
          className='text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4'
          variants={itemVariants}
          whileHover={{ scale: 1.05 }}
          transition={{ duration: 0.2 }}
        >
          🚀 Supercharge Your LinkedIn Game!
        </motion.h1>

        {/* Features Grid */}
        <motion.div
          className='grid grid-cols-1 md:grid-cols-2 gap-4 mb-8'
          variants={containerVariants}
        >
          <motion.div
            className='flex items-center space-x-3 bg-blue-50 p-4 rounded-lg border border-blue-100'
            variants={itemVariants}
            whileHover={{ scale: 1.05, y: -2 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <FileText className='w-8 h-8 text-blue-600' />
            </motion.div>
            <div className='text-left'>
              <motion.h3
                className='font-semibold text-blue-900'
                variants={itemVariants}
              >
                AI-Powered Recommendations
              </motion.h3>
              <motion.p
                className='text-sm text-blue-700'
                variants={itemVariants}
              >
                Get personalized, professional recommendations tailored to your
                industry
              </motion.p>
            </div>
          </motion.div>

          <motion.div
            className='flex items-center space-x-3 bg-purple-50 p-4 rounded-lg border border-purple-100'
            variants={itemVariants}
            whileHover={{ scale: 1.05, y: -2 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <History className='w-8 h-8 text-purple-600' />
            </motion.div>
            <div className='text-left'>
              <motion.h3
                className='font-semibold text-purple-900'
                variants={itemVariants}
              >
                Recommendation History
              </motion.h3>
              <motion.p
                className='text-sm text-purple-700'
                variants={itemVariants}
              >
                Save and manage all your generated recommendations in one place
              </motion.p>
            </div>
          </motion.div>

          <motion.div
            className='flex items-center space-x-3 bg-green-50 p-4 rounded-lg border border-green-100'
            variants={itemVariants}
            whileHover={{ scale: 1.05, y: -2 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <Zap className='w-8 h-8 text-green-600' />
            </motion.div>
            <div className='text-left'>
              <motion.h3
                className='font-semibold text-green-900'
                variants={itemVariants}
              >
                Advanced Customization
              </motion.h3>
              <motion.p
                className='text-sm text-green-700'
                variants={itemVariants}
              >
                Fine-tune tone, length, and style to match your unique voice
              </motion.p>
            </div>
          </motion.div>

          <motion.div
            className='flex items-center space-x-3 bg-orange-50 p-4 rounded-lg border border-orange-100'
            variants={itemVariants}
            whileHover={{ scale: 1.05, y: -2 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <Users className='w-8 h-8 text-orange-600' />
            </motion.div>
            <div className='text-left'>
              <motion.h3
                className='font-semibold text-orange-900'
                variants={itemVariants}
              >
                Professional Templates
              </motion.h3>
              <motion.p
                className='text-sm text-orange-700'
                variants={itemVariants}
              >
                Access curated templates for different industries and roles
              </motion.p>
            </div>
          </motion.div>
        </motion.div>

        <motion.div
          className='bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-lg mb-8 border border-yellow-200'
          variants={itemVariants}
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.2 }}
        >
          <motion.p
            className='text-yellow-800 font-medium'
            variants={itemVariants}
          >
            🎯 <strong>Pro Tip:</strong> You get 3 free recommendations a day!
            Upgrade anytime to unlock unlimited access.
          </motion.p>
        </motion.div>

        <motion.div className='flex flex-col space-y-4' variants={itemVariants}>
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            <Link to='/login' className='w-full'>
              <Button className='w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3 px-6 rounded-lg text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-1'>
                🎉 Sign In & Get Started
              </Button>
            </Link>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            <Link to='/register' className='w-full'>
              <Button
                variant='outline'
                className='w-full border-2 border-purple-600 text-purple-600 hover:bg-purple-50 py-3 px-6 rounded-lg text-lg font-semibold hover:shadow-md transition-all duration-200 transform hover:-translate-y-0.5'
              >
                🌟 Create Free Account
              </Button>
            </Link>
          </motion.div>
        </motion.div>

        <motion.p
          className='text-sm text-gray-500 mt-6'
          variants={itemVariants}
        >
          Join dozens of professionals who&apos;ve boosted their LinkedIn
          profiles! ⭐
        </motion.p>
      </motion.div>
    </motion.div>
  );
};

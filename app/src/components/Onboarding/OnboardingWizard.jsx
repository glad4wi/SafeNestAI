import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../UI/Card';
import Button from '../UI/Button';
import './OnboardingWizard.css';
import { ChevronRight, ChevronLeft, CheckCircle } from 'lucide-react';

const stepsConfig = [
    // 1. Universal Entry
    {
        id: 'role',
        title: 'Are you?',
        type: 'single-select',
        options: [
            { label: 'Buyer / Renter', value: 'buyer_renter', icon: '🏠' },
            { label: 'Professional Inspector', value: 'inspector', icon: '🔍' },
            { label: 'Builder / Developer', value: 'builder', icon: '🏗️' },
            { label: 'Property Manager', value: 'manager', icon: '🏢' },
            { label: 'Insurance / Regulator', value: 'insurance', icon: '⚖️' }
        ]
    },
    {
        id: 'intent',
        title: 'What is your primary goal today?',
        type: 'single-select',
        options: [
            { label: 'Evaluate property safety', value: 'evaluate_safety' },
            { label: 'Perform a professional inspection', value: 'inspection' },
            { label: 'Monitor multiple properties', value: 'monitor' },
            { label: 'Assess compliance or insurance risk', value: 'compliance' }
        ]
    },

    // 2. Property Context (Universal)
    {
        id: 'property_type',
        title: 'Property Type',
        type: 'single-select',
        options: [
            { label: 'Apartment', value: 'apartment' },
            { label: 'Independent House', value: 'house' },
            { label: 'Villa', value: 'villa' },
            { label: 'Under-construction project', value: 'under_construction' },
            { label: 'Commercial property', value: 'commercial' }
        ]
    },
    {
        id: 'property_status',
        title: 'Ownership Status',
        type: 'single-select',
        options: [
            { label: 'Owned', value: 'owned' },
            { label: 'Rented', value: 'rented' },
            { label: 'Under evaluation', value: 'evaluation' }
        ]
    },
    {
        id: 'construction_stage',
        title: 'Construction Stage',
        type: 'single-select',
        options: [
            { label: 'Planning', value: 'planning' },
            { label: 'Under construction', value: 'under_construction' },
            { label: 'Newly built', value: 'newly_built' },
            { label: 'Occupied', value: 'occupied' }
        ]
    },
    {
        id: 'building_age',
        title: 'Building Age',
        type: 'single-select',
        options: [
            { label: '< 1 year', value: '0-1' },
            { label: '1–5 years', value: '1-5' },
            { label: '5–15 years', value: '5-15' },
            { label: '15+ years', value: '15+' }
        ]
    },
    {
        id: 'location_city',
        title: 'Property City / Region',
        type: 'text',
        placeholder: 'e.g. New York, NY'
    },

    // 3. Buyer / Renter Specific
    {
        id: 'stay_duration',
        title: 'Expected Duration of Stay',
        type: 'single-select',
        condition: (data) => data.role === 'buyer_renter',
        options: [
            { label: '< 1 year', value: 'short_term' },
            { label: '1–3 years', value: 'medium_term' },
            { label: '3+ years', value: 'long_term' }
        ]
    },
    {
        id: 'occupant_profile',
        title: 'Who will occupy the property?',
        type: 'multi-select',
        condition: (data) => data.role === 'buyer_renter',
        options: [
            { label: 'Single occupant', value: 'single' },
            { label: 'Couple', value: 'couple' },
            { label: 'Family', value: 'family' },
            { label: 'Children', value: 'children' },
            { label: 'Elderly', value: 'elderly' },
            { label: 'Persons with disabilities', value: 'disabilities' }
        ]
    },
    {
        id: 'risk_priority',
        title: 'What matters most to you?',
        type: 'single-select',
        condition: (data) => data.role === 'buyer_renter',
        options: [
            { label: 'Safety', value: 'safety' },
            { label: 'Maintenance cost', value: 'maintenance' },
            { label: 'Long-term durability', value: 'durability' },
            { label: 'Resale value', value: 'resale' }
        ]
    },

    // 4. Professional Inspector Specific
    {
        id: 'inspector_certification',
        title: 'Certification Level',
        type: 'single-select',
        condition: (data) => data.role === 'inspector',
        options: [
            { label: 'Certified / Licensed', value: 'licensed' },
            { label: 'Master Inspector', value: 'master' },
            { label: 'Trainee / Associate', value: 'trainee' }
        ]
    },
    {
        id: 'inspection_method',
        title: 'Preferred Inspection Method',
        type: 'single-select',
        condition: (data) => data.role === 'inspector',
        options: [
            { label: 'Visual-only', value: 'visual' },
            { label: 'Instrument-assisted', value: 'instrument' },
            { label: 'Compliance-focused', value: 'compliance' }
        ]
    },

    // 5. Builder Specific
    {
        id: 'project_size',
        title: 'Project Size',
        type: 'single-select',
        condition: (data) => data.role === 'builder',
        options: [
            { label: '< 10 units', value: 'small' },
            { label: '10–50 units', value: 'medium' },
            { label: '50+ units', value: 'large' }
        ]
    },
    {
        id: 'builder_priority',
        title: 'Primary Business Concern',
        type: 'single-select',
        condition: (data) => data.role === 'builder',
        options: [
            { label: 'Compliance', value: 'compliance' },
            { label: 'Cost control', value: 'cost' },
            { label: 'Timeline adherence', value: 'timeline' },
            { label: 'Brand reputation', value: 'reputation' }
        ]
    },

    // 8. Document Uploads (Optional)
    {
        id: 'documents',
        title: 'Optional Documents',
        type: 'single-select',
        options: [
            { label: 'Upload Blueprints', value: 'blueprints', icon: '📂' },
            { label: 'Upload Past Inspection', value: 'past_report', icon: '📄' },
            { label: 'Skip for now', value: 'skip', icon: '⏩' }
        ]
    }
];

const OnboardingWizard = ({ onComplete }) => {
    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [formData, setFormData] = useState({});
    const [direction, setDirection] = useState(1);
    const [inputText, setInputText] = useState('');

    // Filter steps based on current formData
    const activeSteps = stepsConfig.filter(step => !step.condition || step.condition(formData));

    // Safety check
    const step = activeSteps[currentStepIndex] || activeSteps[0];

    // Helper to check selection logic
    const isSelected = (value) => {
        if (step.type === 'multi-select') {
            return (formData[step.id] || []).includes(value);
        }
        return formData[step.id] === value;
    };

    const handleSelect = (value) => {
        if (step.type === 'multi-select') {
            const currentValues = formData[step.id] || [];
            const newValues = currentValues.includes(value)
                ? currentValues.filter(v => v !== value)
                : [...currentValues, value];
            setFormData({ ...formData, [step.id]: newValues });
        } else {
            setFormData({ ...formData, [step.id]: value });
        }
    };

    const handleTextChange = (e) => {
        const val = e.target.value;
        setInputText(val);
        setFormData({ ...formData, [step.id]: val });
    };

    const handleNext = () => {
        if (currentStepIndex < activeSteps.length - 1) {
            setDirection(1);
            setCurrentStepIndex(currentStepIndex + 1);

            // Prepare generic input state for next step if relevant
            const nextStep = activeSteps[currentStepIndex + 1];
            if (nextStep && nextStep.type === 'text') {
                setInputText(formData[nextStep.id] || '');
            } else {
                setInputText('');
            }
        } else {
            console.log('Onboarding Complete:', formData);
            if (onComplete) onComplete(formData);
        }
    };

    const handleBack = () => {
        if (currentStepIndex > 0) {
            setDirection(-1);
            setCurrentStepIndex(currentStepIndex - 1);

            const prevStep = activeSteps[currentStepIndex - 1];
            if (prevStep && prevStep.type === 'text') {
                setInputText(formData[prevStep.id] || '');
            } else {
                setInputText('');
            }
        }
    };

    const variants = {
        enter: (direction) => ({
            x: direction > 0 ? 500 : -500,
            opacity: 0
        }),
        center: {
            x: 0,
            opacity: 1
        },
        exit: (direction) => ({
            x: direction < 0 ? 500 : -500,
            opacity: 0
        })
    };

    // Validation for Next button
    const canProceed = () => {
        const val = formData[step.id];
        if (step.type === 'multi-select') {
            return val && val.length > 0;
        }
        if (step.type === 'text') {
            return val && val.trim().length > 0;
        }
        return !!val;
    };

    return (
        <div className="wizard-container">
            <div className="progress-bar">
                <div
                    className="progress-fill"
                    style={{ width: `${((currentStepIndex + 1) / activeSteps.length) * 100}%` }}
                />
            </div>

            <AnimatePresence custom={direction} mode='wait'>
                <motion.div
                    key={step.id}
                    custom={direction}
                    variants={variants}
                    initial="enter"
                    animate="center"
                    exit="exit"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    className="step-content"
                >
                    <Card className="step-card">
                        <div className="step-header">
                            <h2 className="step-title neon-text">{step.title}</h2>
                            <img src="/CH.png" className="step-mascot" alt="AI Assistant" />
                        </div>

                        <div className="step-content-body">
                            {step.type === 'text' ? (
                                <input
                                    type="text"
                                    className="neon-input"
                                    placeholder={step.placeholder}
                                    value={inputText}
                                    onChange={handleTextChange}
                                    autoFocus
                                />
                            ) : (
                                <div className="options-grid">
                                    {step.options.map((option) => {
                                        const selected = isSelected(option.value);
                                        return (
                                            <motion.div
                                                key={option.value}
                                                whileHover={{ scale: 1.02, backgroundColor: 'rgba(10, 26, 255, 0.2)' }}
                                                onClick={() => handleSelect(option.value)}
                                                className={`option-card ${selected ? 'selected' : ''}`}
                                            >
                                                <div className="option-label">
                                                    {option.icon} {option.label}
                                                </div>
                                                {selected && <CheckCircle className="check-icon" />}
                                            </motion.div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>

                        <div className="navigation-buttons">
                            <Button
                                variant="ghost"
                                onClick={handleBack}
                                disabled={currentStepIndex === 0}
                                style={{ opacity: currentStepIndex === 0 ? 0 : 1 }}
                            >
                                <ChevronLeft size={20} /> Back
                            </Button>
                            <Button
                                variant="primary"
                                onClick={handleNext}
                                disabled={!canProceed()}
                            >
                                Next <ChevronRight size={20} />
                            </Button>
                        </div>
                    </Card>
                </motion.div>
            </AnimatePresence>
        </div>
    );
};

export default OnboardingWizard;

import re


class AiRecruiter:
    STOP_WORDS = {
        'the', 'and', 'is', 'in', 'at', 'of', 'for', 'with', 'a', 'an', 'to',
        'we', 'are', 'you', 'will', 'be', 'or', 'as', 'on', 'our', 'your',
        'this', 'that', 'from', 'by', 'have', 'has', 'can', 'should', 'work',
        'job', 'team', 'role', 'looking', 'skills', 'experience', 'knowledge',
        'ability', 'must', 'required',
    }

    CATEGORY_BASE_SALARY = {
        'IT': 60000, 'Software': 75000, 'Management': 80000,
        'Marketing': 45000, 'Accounting': 50000, 'Engineering': 65000,
        'Sales': 35000, 'Clerical': 30000, 'Driver': 40000, 'Teacher': 35000,
    }

    def score_cv(self, cv_text, job_description, candidate_exp=0, required_exp=0):
        cv_lower = re.sub(r'<[^>]+>', '', cv_text).lower()
        jd_lower = re.sub(r'<[^>]+>', '', job_description).lower()

        keywords = self._extract_keywords(jd_lower)
        if not keywords:
            return {'score': 0, 'matches': [], 'recommendation': 'Job description too short'}

        matches = self._keyword_matches(cv_lower, keywords)
        keyword_score = min(100, (len(matches) / len(keywords)) * 2 * 100)
        exp_score = self._experience_score(candidate_exp, required_exp)
        final = round(min(100, keyword_score * 0.7 + exp_score * 0.3))

        return {
            'score': final,
            'matches': matches[:5],
            'recommendation': self._recommendation(final),
        }

    def estimate_salary(self, cv_text, experience_years, job_category=''):
        cv_lower = re.sub(r'<[^>]+>', '', cv_text).lower()
        base = 40000
        for key, val in self.CATEGORY_BASE_SALARY.items():
            if key.lower() in job_category.lower():
                base = val
                break

        exp_mult = 1 + (min(experience_years, 5) * 0.20) + (max(experience_years - 5, 0) * 0.10)
        bonus = 0
        if 'phd' in cv_lower:
            bonus += 0.5
        elif 'master' in cv_lower or 'mba' in cv_lower:
            bonus += 0.3
        elif any(w in cv_lower for w in ('degree', 'bsc', 'bachelor')):
            bonus += 0.15
        if any(w in cv_lower for w in ('senior', 'lead', 'manager')):
            bonus += 0.2

        estimated = base * (exp_mult + bonus)
        return round(estimated / 5000) * 5000

    def _extract_keywords(self, text):
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        words = [w.strip() for w in text.split()]
        return list({w for w in words if len(w) > 2 and w not in self.STOP_WORDS and not w.isdigit()})

    def _keyword_matches(self, cv_text, keywords):
        return [w for w in keywords if re.search(r'\b' + re.escape(w) + r'\b', cv_text)]

    def _experience_score(self, candidate, required):
        if required > 0:
            return min(100, (candidate / required) * 100)
        return 100 if candidate >= 1 else 50

    def _recommendation(self, score):
        if score > 80:
            return 'Excellent Match'
        if score > 60:
            return 'Good Match'
        if score > 40:
            return 'Potential Match'
        return 'Low Match'
